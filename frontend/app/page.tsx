'use client';

import { useState, useEffect } from 'react';

interface FileData {
  file_id: string;
  filename: string;
  columns: string[];
  row_count: number;
  preview: any[];
}

interface ConvertResult {
  file_id: string;
  status: string;
  segments: number;
  claims_count: number;
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [fileData, setFileData] = useState<FileData | null>(null);
  const [converting, setConverting] = useState(false);
  const [result, setResult] = useState<ConvertResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [apiStatus, setApiStatus] = useState<string>('checking...');

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(data => setApiStatus('connected'))
      .catch(() => setApiStatus('disconnected'));
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
      setResult(null);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    
    setError(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error('Upload failed');
      }
      
      const data = await response.json();
      setFileData(data);
    } catch (err) {
      setError('Failed to upload file. Make sure the API is running.');
    }
  };

  const handleConvert = async () => {
    if (!fileData) return;
    
    setConverting(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/convert', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_id: fileData.file_id,
        }),
      });
      
      if (!response.ok) {
        throw new Error('Conversion failed');
      }
      
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError('Failed to convert file.');
    } finally {
      setConverting(false);
    }
  };

  const handleDownload = () => {
    if (!result) return;
    window.open(`http://localhost:8000/download/${result.file_id}`, '_blank');
  };

  return (
    <main style={{ maxWidth: '800px', margin: '0 auto', padding: '2rem', fontFamily: 'system-ui' }}>
      <header style={{ marginBottom: '2rem', borderBottom: '1px solid #eee', paddingBottom: '1rem' }}>
        <h1 style={{ margin: 0 }}>🏥 Bulk 837 Medical Claims Converter</h1>
        <p style={{ color: '#666', marginTop: '0.5rem' }}>
          Convert CSV files to X12 837P EDI format for medical billing
        </p>
        <div style={{ fontSize: '0.875rem', color: apiStatus === 'connected' ? 'green' : 'red' }}>
          API Status: {apiStatus}
        </div>
      </header>

      <section style={{ marginBottom: '2rem' }}>
        <h2>1. Upload CSV</h2>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <input 
            type="file" 
            accept=".csv" 
            onChange={handleFileChange}
            style={{ padding: '0.5rem' }}
          />
          <button 
            onClick={handleUpload}
            disabled={!file}
            style={{
              padding: '0.5rem 1rem',
              background: file ? '#0070f3' : '#ccc',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: file ? 'pointer' : 'not-allowed'
            }}
          >
            Upload
          </button>
        </div>
      </section>

      {error && (
        <div style={{ padding: '1rem', background: '#fee', borderRadius: '4px', marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      {fileData && (
        <section style={{ marginBottom: '2rem' }}>
          <h2>2. File Preview</h2>
          <div style={{ background: '#f5f5f5', padding: '1rem', borderRadius: '4px' }}>
            <p><strong>File:</strong> {fileData.filename}</p>
            <p><strong>Rows:</strong> {fileData.row_count}</p>
            <p><strong>Columns:</strong> {fileData.columns.join(', ')}</p>
          </div>
          
          <h3>Data Preview</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <thead>
              <tr>
                {fileData.columns.map(col => (
                  <th key={col} style={{ border: '1px solid #ddd', padding: '0.5rem', background: '#eee' }}>
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {fileData.preview.map((row, i) => (
                <tr key={i}>
                  {fileData.columns.map(col => (
                    <td key={col} style={{ border: '1px solid #ddd', padding: '0.5rem' }}>
                      {row[col] ?? ''}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {fileData && (
        <section style={{ marginBottom: '2rem' }}>
          <h2>3. Convert to 837P</h2>
          <button 
            onClick={handleConvert}
            disabled={converting}
            style={{
              padding: '0.75rem 2rem',
              background: converting ? '#ccc' : '#10a010',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '1rem',
              cursor: converting ? 'not-allowed' : 'pointer'
            }}
          >
            {converting ? 'Converting...' : 'Generate 837P EDI'}
          </button>
        </section>
      )}

      {result && (
        <section>
          <h2>4. Download</h2>
          <div style={{ background: '#dfd', padding: '1rem', borderRadius: '4px', marginBottom: '1rem' }}>
            <p><strong>Status:</strong> {result.status}</p>
            <p><strong>Segments:</strong> {result.segments}</p>
            <p><strong>Claims:</strong> {result.claims_count}</p>
          </div>
          <button 
            onClick={handleDownload}
            style={{
              padding: '0.75rem 2rem',
              background: '#0070f3',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '1rem',
              cursor: 'pointer'
            }}
          >
            Download .EDI File
          </button>
        </section>
      )}

      <footer style={{ marginTop: '3rem', paddingTop: '1rem', borderTop: '1px solid #eee', fontSize: '0.875rem', color: '#666' }}>
        <p>Note: This tool generates 837P files for manual upload to clearinghouses/payers.</p>
      </footer>
    </main>
  );
}
