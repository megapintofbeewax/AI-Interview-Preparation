import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ErrorAlert from '../components/ErrorAlert';

export default function ResumeUpload() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [uploadedResumeInfo, setUploadedResumeInfo] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  const validateAndSetFile = (file) => {
    if (!file) return;

    const ext = file.name.split('.').pop().toLowerCase();
    if (ext !== 'pdf' && ext !== 'docx') {
      setError('Unsupported file format. Please upload a PDF or DOCX document.');
      setSelectedFile(null);
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError('File size exceeds the 10 MB limit.');
      setSelectedFile(null);
      return;
    }

    setError('');
    setSelectedFile(file);
    setUploadSuccess(false);
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    validateAndSetFile(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer?.files?.[0];
    validateAndSetFile(file);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please choose a resume file to upload.');
      return;
    }

    setError('');
    setUploading(true);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('/api/resume/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Unable to upload resume. Please try again.');
      }

      setUploadedResumeInfo(data);
      setUploadSuccess(true);
    } catch (err) {
      setError(err.message || 'Unable to upload resume. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col justify-center items-center px-4 py-10 sm:py-16 relative">
      {/* Cinematic Amber Light Orb */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[550px] h-[380px] bg-amber-500/[0.09] blur-[140px] rounded-full pointer-events-none -z-10" />

      <div className="w-full max-w-xl">
        {/* Header */}
        <div className="text-center mb-8 space-y-2">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-[11px] font-mono tracking-widest uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            <span>Document Ingestion // Pipeline</span>
          </div>
          <h1 className="font-heading text-3xl sm:text-4xl font-extrabold tracking-tight text-[#FAFAF5]">
            Upload Resume
          </h1>
          <p className="text-xs text-[#A1A1AA] max-w-md mx-auto">
            Ingest your CV into the neural parser to automatically extract technical entities and customize interview questions
          </p>
        </div>

        {/* Upload Container: Prominent Dark Glass Panel */}
        <div className="glass-panel p-7 sm:p-9 shadow-glass-panel border border-white/12 relative overflow-hidden">
          {/* Top illuminated edge */}
          <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-amber-500/50 to-transparent" />

          {error && (
            <div className="mb-6">
              <ErrorAlert
                title="Unable to process document"
                message={error}
                onRetry={selectedFile ? handleUpload : null}
                retryLabel="Try Again"
              />
            </div>
          )}

          {!uploadSuccess ? (
            <form onSubmit={handleUpload} className="space-y-6">
              {/* Translucent Inset Dropzone with Dashed Amber Border & Glow */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`flex flex-col items-center justify-center p-8 sm:p-10 border-2 border-dashed rounded-card transition-all duration-normal cursor-pointer relative group ${
                  isDragging
                    ? 'border-amber-400 bg-amber-500/15 shadow-amber-glow scale-[1.01]'
                    : selectedFile
                    ? 'border-amber-500/50 bg-amber-500/[0.06] shadow-amber-glow-sm'
                    : 'border-white/15 hover:border-amber-500/50 bg-white/[0.03] hover:bg-white/[0.06]'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  onChange={handleFileChange}
                  className="hidden"
                  id="resume-file-input"
                />

                {/* Expressive Upload Icon with Amber Aura */}
                <div className="w-12 h-12 rounded-full bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400 mb-4 shadow-amber-glow-sm group-hover:scale-105 transition-transform">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>

                <div className="btn-secondary text-xs px-4 py-2 mb-3 pointer-events-none group-hover:border-amber-500/50">
                  {selectedFile ? 'Change Selected Document' : 'Browse Files or Drag & Drop'}
                </div>

                {selectedFile ? (
                  <div className="text-center mt-1">
                    <p className="text-sm font-semibold text-[#FAFAF5] font-mono flex items-center justify-center space-x-1.5">
                      <span className="text-amber-400">📄</span>
                      <span>{selectedFile.name}</span>
                    </p>
                    <p className="text-[11px] text-amber-400/90 mt-1 font-mono">
                      {(selectedFile.size / 1024).toFixed(1)} KB • Ready for Ingestion
                    </p>
                  </div>
                ) : (
                  <div className="text-center space-y-1">
                    <p className="text-xs text-[#FAFAF5] font-medium">Supports PDF or Word DOCX</p>
                    <p className="text-[11px] text-[#71717A]">Maximum file size: 10 MB</p>
                  </div>
                )}
              </div>

              {/* Sample Resumes Section with Amber Accents */}
              <div className="p-3.5 rounded-control bg-white/[0.03] border border-white/5 flex flex-col sm:flex-row items-center justify-between text-xs text-[#A1A1AA] gap-2">
                <span className="text-[11px] uppercase font-mono tracking-wider text-[#71717A]">Testing Templates:</span>
                <div className="flex items-center space-x-3">
                  <a
                    href="/sample_resume.pdf"
                    download="sample_resume.pdf"
                    className="font-medium text-amber-400 hover:text-amber-300 underline underline-offset-2 transition-colors flex items-center space-x-1"
                  >
                    <span>Download PDF</span>
                    <span className="text-[10px]">↓</span>
                  </a>
                  <span className="text-white/20">•</span>
                  <a
                    href="/sample_resume.docx"
                    download="sample_resume.docx"
                    className="font-medium text-amber-400 hover:text-amber-300 underline underline-offset-2 transition-colors flex items-center space-x-1"
                  >
                    <span>Download DOCX</span>
                    <span className="text-[10px]">↓</span>
                  </a>
                </div>
              </div>

              {/* Primary Upload Button */}
              <button
                type="submit"
                disabled={!selectedFile || uploading}
                className="btn-primary w-full py-3.5"
              >
                {uploading ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-[#09090B] border-t-transparent rounded-full animate-spin" />
                    <span>Parsing & Vectorizing Document...</span>
                  </div>
                ) : (
                  'Upload & Parse Resume →'
                )}
              </button>

              <button
                type="button"
                onClick={() => navigate('/resume-analysis')}
                className="w-full text-center text-xs text-[#A1A1AA] hover:text-[#FAFAF5] transition-colors py-2 cursor-pointer"
              >
                Skip to Existing Resume Analysis →
              </button>
            </form>
          ) : (
            /* Clean Success Confirmation */
            <div className="space-y-6 text-center animate-fade-in-up">
              <div className="p-6 rounded-card bg-amber-500/10 border border-amber-500/30 shadow-amber-glow-sm">
                <div className="w-10 h-10 mx-auto mb-3 bg-amber-500/20 border border-amber-500/40 text-amber-400 rounded-full flex items-center justify-center text-base font-bold shadow-amber-glow-sm">
                  ✓
                </div>
                <h3 className="text-base font-heading font-bold text-[#FAFAF5]">
                  Document Parsed & Extracted Successfully
                </h3>
                {uploadedResumeInfo?.filename && (
                  <p className="text-xs text-amber-300 mt-1 font-mono">
                    {uploadedResumeInfo.filename}
                  </p>
                )}
              </div>

              {/* Primary Next Action */}
              <button
                onClick={() => navigate('/resume-analysis')}
                className="btn-primary w-full py-3.5 flex items-center justify-center space-x-2"
              >
                <span>View Extracted Entities & Skills →</span>
              </button>

              {/* Option to re-upload */}
              <button
                type="button"
                onClick={() => {
                  setUploadSuccess(false);
                  setSelectedFile(null);
                }}
                className="text-xs text-[#A1A1AA] hover:text-[#FAFAF5] underline underline-offset-2 transition-colors cursor-pointer"
              >
                Upload a different document
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
