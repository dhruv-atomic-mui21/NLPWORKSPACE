import React, { useState, useEffect } from 'react';

const API_BASE_URL = 'http://localhost:5000';

function SentimentPieChart({ scores }) {
  if (!scores || typeof scores.pos !== 'number' || typeof scores.neu !== 'number' || typeof scores.neg !== 'number') {
    return <div>No sentiment data available.</div>;
  }

  const total = scores.pos + scores.neu + scores.neg;
  if (total === 0) {
    return <div>No sentiment data available.</div>;
  }

  // Calculate angles in degrees
  const posAngle = (scores.pos / total) * 360;
  const neuAngle = (scores.neu / total) * 360;
  const negAngle = (scores.neg / total) * 360;

  // Helper function to create SVG arc path
  const describeArc = (x, y, radius, startAngle, endAngle) => {
    const rad = (angle) => (angle * Math.PI) / 180;
    const start = {
      x: x + radius * Math.cos(rad(startAngle)),
      y: y + radius * Math.sin(rad(startAngle)),
    };
    const end = {
      x: x + radius * Math.cos(rad(endAngle)),
      y: y + radius * Math.sin(rad(endAngle)),
    };
    const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1';
    return [
      `M ${x} ${y}`,
      `L ${start.x} ${start.y}`,
      `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${end.x} ${end.y}`,
      'Z',
    ].join(' ');
  };

  let startAngle = 0;
  const posPath = describeArc(100, 100, 80, startAngle, (startAngle += posAngle));
  const neuPath = describeArc(100, 100, 80, startAngle, (startAngle += neuAngle));
  const negPath = describeArc(100, 100, 80, startAngle, (startAngle += negAngle));

  const legendItemStyle = {
    display: 'flex',
    alignItems: 'center',
    marginBottom: 6,
    fontSize: 14,
    color: '#e0e0e0',
  };

  const colorBoxStyle = (color) => ({
    width: 16,
    height: 16,
    backgroundColor: color,
    marginRight: 8,
    borderRadius: 3,
  });

  return (
    <div>
      <svg width="200" height="200" viewBox="0 0 200 200">
        <path d={posPath} fill="#2196f3" />
        <path d={neuPath} fill="#9e9e9e" />
        <path d={negPath} fill="#f44336" />
      </svg>
      <div style={{ marginTop: 10 }}>
        <div style={legendItemStyle}>
          <div style={colorBoxStyle('#2196f3')} /> Positive: {(scores.pos * 100).toFixed(1)}%
        </div>
        <div style={legendItemStyle}>
          <div style={colorBoxStyle('#9e9e9e')} /> Neutral: {(scores.neu * 100).toFixed(1)}%
        </div>
        <div style={legendItemStyle}>
          <div style={colorBoxStyle('#f44336')} /> Negative: {(scores.neg * 100).toFixed(1)}%
        </div>
      </div>
    </div>
  );
}

function App() {
  const [inputText, setInputText] = useState('');
  const [language, setLanguage] = useState('en-US');
  const [modules, setModules] = useState([]);
  const [selectedModules, setSelectedModules] = useState([]);
  const [results, setResults] = useState(null);
  const [audioFile, setAudioFile] = useState(null);
  const [audioResults, setAudioResults] = useState(null);
  const [saveFilename, setSaveFilename] = useState('');
  const [saveMessage, setSaveMessage] = useState('');
  const [fileList, setFileList] = useState([]);
  const [loadMessage, setLoadMessage] = useState('');
  const [fileContent, setFileContent] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    fetchModules();
    fetchFileList();
  }, []);

  const fetchModules = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/modules`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      if (data.modules) {
        setModules(data.modules);
        // Exclude 'voice' module from selectedModules by default
        const defaultSelected = data.modules.filter((mod) => mod.toLowerCase() !== 'voice');
        setSelectedModules(defaultSelected);
      } else {
        setErrorMessage('No modules data received from server.');
      }
    } catch (error) {
      console.error('Failed to fetch modules:', error);
      setErrorMessage('Failed to fetch modules from server.');
    }
  };

  const fetchFileList = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/load`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      if (data.files) {
        setFileList(data.files);
      } else {
        setErrorMessage('No files data received from server.');
      }
    } catch (error) {
      console.error('Failed to fetch file list:', error);
      setErrorMessage('Failed to fetch file list from server.');
    }
  };

  const handleModuleChange = (moduleName) => {
    setSelectedModules((prev) =>
      prev.includes(moduleName)
        ? prev.filter((m) => m !== moduleName)
        : [...prev, moduleName]
    );
  };

  const processText = async () => {
    if (!inputText) {
      setResults('Please enter some text to process.');
      return;
    }
    setResults('Processing...');
    setErrorMessage('');
    try {
      const response = await fetch(`${API_BASE_URL}/api/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: inputText,
          language,
          modules: selectedModules,
        }),
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(`Server error: ${text}`);
      }
      const data = await response.json();
      setResults(data);
    } catch (error) {
      setResults(null);
      setErrorMessage(`Error processing text: ${error.message}`);
    }
  };

  const handleAudioUpload = async () => {
    if (!audioFile) return;
    setAudioResults('Uploading and processing audio...');
    setErrorMessage('');
    const formData = new FormData();
    formData.append('file', audioFile);
    formData.append('language', language);
    try {
      const response = await fetch(`${API_BASE_URL}/api/upload_audio`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(`Server error: ${text}`);
      }
      const data = await response.json();
      setAudioResults(data);
    } catch (error) {
      setAudioResults(null);
      setErrorMessage(`Error processing audio: ${error.message}`);
    }
  };

  const saveText = async () => {
    if (!inputText || !saveFilename) {
      setSaveMessage('Please enter text and a filename to save.');
      return;
    }
    setSaveMessage('Saving...');
    setErrorMessage('');
    try {
      const response = await fetch(`${API_BASE_URL}/api/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: inputText, filename: saveFilename }),
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(`Server error: ${text}`);
      }
      const data = await response.json();
      if (data.success) {
        setSaveMessage(`Saved to ${data.path}`);
        fetchFileList();
      } else {
        setSaveMessage(`Error saving: ${data.error}`);
      }
    } catch (error) {
      setSaveMessage('');
      setErrorMessage(`Failed to save: ${error.message}`);
    }
  };

  const loadFile = async (filename) => {
    if (!filename) {
      setLoadMessage('Please select a file to load.');
      return;
    }
    setLoadMessage('Loading...');
    setErrorMessage('');
    try {
      const response = await fetch(`${API_BASE_URL}/api/load/${filename}`);
      if (!response.ok) {
        const text = await response.text();
        throw new Error(`Server error: ${text}`);
      }
      const data = await response.json();
      if (data.text) {
        setInputText(data.text);
        setFileContent(data.text);
        setLoadMessage('');
      } else {
        setLoadMessage(`Error loading: ${data.error}`);
        setFileContent('');
      }
    } catch (error) {
      setLoadMessage('');
      setFileContent('');
      setErrorMessage(`Failed to load: ${error.message}`);
    }
  };

  const renderResultValue = (value, moduleName) => {
    if (value === null || value === undefined) {
      return <em>null</em>;
    }
    if (moduleName === 'completion' && typeof value === 'string') {
      return value.replace(/\*\*/g, '');
    }
    if (moduleName === 'grammar' && value.corrected_text) {
      return value.corrected_text;
    }
    if (moduleName === 'sentiment') {
      if (value && typeof value === 'object' && value.scores) {
        return <SentimentPieChart scores={value.scores} />;
      }
      return <div>No sentiment data available.</div>;
    }
    if (typeof value === 'string') {
      return value;
    }
    if (typeof value === 'number' || typeof value === 'boolean') {
      return value.toString();
    }
    if (Array.isArray(value)) {
      return (
        <ul>
          {value.map((item, idx) => (
            <li key={idx}>{renderResultValue(item)}</li>
          ))}
        </ul>
      );
    }
    if (typeof value === 'object') {
      const filteredEntries = Object.entries(value).filter(
        ([key, _]) =>
          ![
            'length',
            'size',
            'count',
            'issues',
            'message',
            'offset',
            'replacements',
            'rule_id',
          ].includes(key.toLowerCase())
      );
      if (filteredEntries.length === 1 && typeof filteredEntries[0][1] !== 'object') {
        return renderResultValue(filteredEntries[0][1]);
      }
      return (
        <ul>
          {filteredEntries.map(([k, v]) => (
            <li key={k}>
              <strong>{k}:</strong> {renderResultValue(v)}
            </li>
          ))}
        </ul>
      );
    }
    return value.toString();
  };

  // Dark mode styles
  const darkTheme = {
    backgroundColor: '#121212',
    color: '#e0e0e0',
    minHeight: '100vh',
    padding: '20px',
    fontFamily: 'Arial, sans-serif',
  };

  const sectionStyle = {
    marginBottom: 30,
  };

  const textareaStyle = {
    width: '100%',
    minHeight: 120,
    padding: 12,
    fontSize: 16,
    backgroundColor: '#1e1e1e',
    color: '#e0e0e0',
    border: '1px solid #333',
    borderRadius: 4,
  };

  const selectStyle = {
    marginLeft: 10,
    fontSize: 16,
    padding: 4,
    backgroundColor: '#1e1e1e',
    color: '#e0e0e0',
    border: '1px solid #333',
    borderRadius: 4,
  };

  const buttonStyle = {
    marginLeft: 20,
    padding: '8px 20px',
    fontSize: 16,
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: 4,
    cursor: 'pointer',
  };

  const checkboxLabelStyle = {
    fontSize: 16,
  };

  const resultsContainerStyle = {
    backgroundColor: '#1e1e1e',
    padding: 15,
    borderRadius: 6,
    minHeight: 100,
    fontSize: 15,
    whiteSpace: 'pre-wrap',
    color: '#e0e0e0',
  };

  return (
    <div style={darkTheme}>
      <h1>Smart NLP Workspace</h1>

      {errorMessage && (
        <div style={{ color: '#ff6b6b', marginBottom: 20, fontWeight: 'bold' }}>{errorMessage}</div>
      )}

      <section style={sectionStyle}>
        <h2>Enter Text for Analysis</h2>
        <textarea
          style={textareaStyle}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Type or paste your text here..."
        />
        <div style={{ marginTop: 15 }}>
          <label>
            Select Language:
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              style={selectStyle}
            >
              <option value="en-US">English (United States)</option>
              <option value="en-GB">English (United Kingdom)</option>
              <option value="fr-FR">Français (French)</option>
              <option value="de-DE">Deutsch (German)</option>
              <option value="es-ES">Español (Spanish)</option>
              <option value="it-IT">Italiano (Italian)</option>
              <option value="nl-NL">Nederlands (Dutch)</option>
              <option value="pt-PT">Português (Portuguese)</option>
              <option value="ru-RU">Русский (Russian)</option>
              <option value="zh-CN">中文 (Chinese)</option>
              <option value="ja-JP">日本語 (Japanese)</option>
              <option value="pl-PL">Polski (Polish)</option>
              <option value="sv-SE">Svenska (Swedish)</option>
              <option value="tr-TR">Türkçe (Turkish)</option>
              <option value="uk-UA">Українська (Ukrainian)</option>
              <option value="cs-CZ">Čeština (Czech)</option>
              <option value="da-DK">Dansk (Danish)</option>
              <option value="fi-FI">Suomi (Finnish)</option>
              <option value="el-GR">Ελληνικά (Greek)</option>
              <option value="hu-HU">Magyar (Hungarian)</option>
              <option value="ro-RO">Română (Romanian)</option>
              <option value="sk-SK">Slovenčina (Slovak)</option>
              <option value="bg-BG">Български (Bulgarian)</option>
              <option value="hr-HR">Hrvatski (Croatian)</option>
              <option value="lt-LT">Lietuvių (Lithuanian)</option>
              <option value="lv-LV">Latviešu (Latvian)</option>
              <option value="et-EE">Eesti (Estonian)</option>
              <option value="sl-SI">Slovenščina (Slovenian)</option>
              <option value="he-IL">עברית (Hebrew)</option>
              <option value="ar-SA">العربية (Arabic)</option>
              <option value="hi-IN">हिन्दी (Hindi)</option>
              <option value="th-TH">ไทย (Thai)</option>
              <option value="vi-VN">Tiếng Việt (Vietnamese)</option>
            </select>
          </label>
          <button onClick={processText} style={buttonStyle}>
            Process Text
          </button>
        </div>
      </section>

      <section style={sectionStyle}>
        <h2>Choose NLP Modules</h2>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 15 }}>
          {modules.length > 0 ? (
            modules.map((mod) => (
              <label key={mod} style={checkboxLabelStyle}>
                <input
                  type="checkbox"
                  checked={selectedModules.includes(mod)}
                  onChange={() => handleModuleChange(mod)}
                  style={{ marginRight: 6 }}
                />
                {mod}
              </label>
            ))
          ) : (
            <p>No modules available.</p>
          )}
        </div>
      </section>

      <section style={sectionStyle}>
        <h2>Analysis Results</h2>
        <div style={resultsContainerStyle}>
          {typeof results === 'string' ? (
            <p>{results}</p>
          ) : results ? (
            Object.entries(results).map(([moduleName, result]) => (
              <div key={moduleName} style={{ marginBottom: 20 }}>
                <h3 style={{ borderBottom: '1px solid #444', paddingBottom: 4, color: '#e0e0e0' }}>
                  {moduleName}
                </h3>
                {renderResultValue(result, moduleName)}
              </div>
            ))
          ) : (
            <p>No results yet.</p>
          )}
        </div>
      </section>

      <section style={sectionStyle}>
        <h2>Audio Processing</h2>
        <input
          type="file"
          accept="audio/*"
          onChange={(e) => setAudioFile(e.target.files[0])}
          style={{ fontSize: 16 }}
        />
        <button
          onClick={handleAudioUpload}
          disabled={!audioFile}
          style={{
            marginLeft: 15,
            padding: '8px 20px',
            fontSize: 16,
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: 4,
            cursor: 'pointer',
          }}
        >
          Upload Audio
        </button>
        <div
          style={{
            marginTop: 15,
            backgroundColor: '#2a2a2a',
            padding: 10,
            borderRadius: 4,
            minHeight: 80,
            fontSize: 14,
            whiteSpace: 'pre-wrap',
            color: '#e0e0e0',
          }}
        >
          {audioResults && (typeof audioResults === 'string' ? audioResults : JSON.stringify(audioResults, null, 2))}
        </div>
      </section>

      <section style={sectionStyle}>
        <h2>Save and Load Your Texts</h2>
        <div style={{ marginBottom: 15 }}>
          <input
            type="text"
            placeholder="Enter filename to save"
            value={saveFilename}
            onChange={(e) => setSaveFilename(e.target.value)}
            style={{ padding: 8, fontSize: 16, width: '60%', marginRight: 10, backgroundColor: '#1e1e1e', color: '#e0e0e0', border: '1px solid #333', borderRadius: 4 }}
          />
          <button
            onClick={saveText}
            style={{
              padding: '8px 20px',
              fontSize: 16,
              backgroundColor: '#17a2b8',
              color: 'white',
              border: 'none',
              borderRadius: 4,
              cursor: 'pointer',
            }}
          >
            Save
          </button>
          <div style={{ marginTop: 8, fontSize: 14, color: '#4caf50' }}>{saveMessage}</div>
        </div>
        <div>
          <select
            onChange={(e) => loadFile(e.target.value)}
            defaultValue=""
            style={{ padding: 8, fontSize: 16, width: '60%', backgroundColor: '#1e1e1e', color: '#e0e0e0', border: '1px solid #333', borderRadius: 4 }}
          >
            <option value="" disabled>
              Select a file to load
            </option>
            {fileList.map((file) => (
              <option key={file} value={file}>
                {file}
              </option>
            ))}
          </select>
          <div
            style={{
              marginTop: 10,
              backgroundColor: '#2a2a2a',
              padding: 10,
              borderRadius: 4,
              border: '1px solid #444',
              minHeight: 100,
              whiteSpace: 'pre-wrap',
              fontSize: 15,
              color: '#e0e0e0',
            }}
          >
            {fileContent}
          </div>
          <div style={{ marginTop: 8, fontSize: 14, color: '#ff6b6b' }}>{loadMessage}</div>
        </div>
      </section>
    </div>
  );
}

export default App;
