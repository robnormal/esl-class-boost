import React, { useState } from 'react';

function SubmissionForm() {
  const [inputType, setInputType] = useState<'file' | 'url' | 'text'>('file');
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState('');
  const [text, setText] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputType === 'file' && file) {
      console.log('Submitting file:', file);
    } else if (inputType === 'url' && url) {
      console.log('Submitting URL:', url);
    } else if (inputType === 'text' && text) {
      console.log('Submitting text:', text);
    } else {
      alert('Please provide input.');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h3>Submit Your Material</h3>

      <div>
        <label>
          <input
            type="radio"
            name="inputType"
            value="file"
            checked={inputType === 'file'}
            onChange={() => setInputType('file')}
          />
          Upload File
        </label>
        <label>
          <input
            type="radio"
            name="inputType"
            value="url"
            checked={inputType === 'url'}
            onChange={() => setInputType('url')}
          />
          URL to File
        </label>
        <label>
          <input
            type="radio"
            name="inputType"
            value="text"
            checked={inputType === 'text'}
            onChange={() => setInputType('text')}
          />
          Paste Text
        </label>
      </div>

      {inputType === 'file' && (
        <div>
          <input
            type="file"
            accept=".txt,.pdf,.docx,.html,.md,.png,.jpg"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </div>
      )}

      {inputType === 'url' && (
        <div>
          <input
            type="text"
            placeholder="https://example.com/file.pdf"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
        </div>
      )}

      {inputType === 'text' && (
        <div>
          <textarea
            rows={10}
            cols={80}
            placeholder="Paste your text here..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
        </div>
      )}

      <button type="submit">Submit</button>
    </form>
  );
}

export default SubmissionForm;
