import { useEffect, useState, useRef } from 'react';
import { documentsAPI } from '../api/client';
import { UploadCloud, FileText, CheckCircle, XCircle, Loader, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';
import { format } from 'date-fns';

const SOURCE_TYPES = ['policy', 'sop', 'regulation', 'contract', 'report', 'other'];

export default function DocumentsPage() {
  const [docs, setDocs]         = useState([]);
  const [loading, setLoading]   = useState(true);
  const [uploading, setUploading] = useState(false);
  const [sourceType, setSourceType] = useState('policy');
  const [dragging, setDragging] = useState(false);
  const fileRef = useRef();

  const fetchDocs = () => {
    setLoading(true);
    documentsAPI.list()
      .then(r => setDocs(r.data))
      .catch(() => toast.error('Failed to load documents'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchDocs(); }, []);

  const uploadFile = async (file) => {
    if (!file) return;
    const allowed = ['.pdf', '.docx', '.txt', '.md'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowed.includes(ext)) {
      toast.error(`Unsupported type: ${ext}. Allowed: ${allowed.join(', ')}`);
      return;
    }
    setUploading(true);
    try {
      const { data } = await documentsAPI.upload(file, sourceType);
      toast.success(`✓ Ingested "${data.filename}" — ${data.chunks_indexed} chunks indexed`);
      fetchDocs();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const onFileChange = (e) => { uploadFile(e.target.files[0]); e.target.value = ''; };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    uploadFile(e.dataTransfer.files[0]);
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Document Ingestion</h1>
          <p className="page-sub">Upload policies, SOPs, and regulations into the RAG knowledge base</p>
        </div>
        <button className="btn-ghost" onClick={fetchDocs}>
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {/* Upload area */}
      <div
        className={`upload-zone ${dragging ? 'dragging' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !uploading && fileRef.current.click()}
      >
        <input ref={fileRef} type="file" accept=".pdf,.docx,.txt,.md" hidden onChange={onFileChange} />
        {uploading ? (
          <div className="upload-zone-inner">
            <Loader size={40} className="spin upload-icon" />
            <p>Ingesting into Pinecone vector store…</p>
          </div>
        ) : (
          <div className="upload-zone-inner">
            <UploadCloud size={40} className="upload-icon" />
            <p className="upload-title">Drop a file here or <span className="upload-link">browse</span></p>
            <p className="upload-sub">PDF, DOCX, TXT, MD — chunked &amp; embedded automatically</p>
          </div>
        )}
      </div>

      {/* Source type selector */}
      <div className="source-type-row">
        <label className="source-type-label">Document type:</label>
        <div className="source-type-pills">
          {SOURCE_TYPES.map(t => (
            <button
              key={t}
              className={`pill ${sourceType === t ? 'active' : ''}`}
              onClick={() => setSourceType(t)}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Documents table */}
      <div className="table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Filename</th>
              <th>Type</th>
              <th>Chunks</th>
              <th>Status</th>
              <th>Uploaded</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 4 }).map((_, i) => (
                <tr key={i}><td colSpan={5}><div className="row-skeleton" /></td></tr>
              ))
            ) : docs.length === 0 ? (
              <tr><td colSpan={5} className="empty-row">No documents yet. Upload your first file above.</td></tr>
            ) : (
              docs.map((d) => (
                <tr key={d.id}>
                  <td className="td-filename"><FileText size={14} /> {d.filename}</td>
                  <td><span className="pill active">{d.source_type}</span></td>
                  <td>{d.chunk_count}</td>
                  <td>
                    {d.status === 'processed'
                      ? <span className="status-ok"><CheckCircle size={14} /> Processed</span>
                      : <span className="status-err"><XCircle size={14} /> Failed</span>
                    }
                  </td>
                  <td className="td-date">{format(new Date(d.uploaded_at), 'MMM d, yyyy HH:mm')}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
