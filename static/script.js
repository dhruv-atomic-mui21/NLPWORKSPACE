document.addEventListener('DOMContentLoaded', () => {
    const inputText = document.getElementById('inputText');
    const languageSelect = document.getElementById('language');
    const processButton = document.getElementById('processButton');
    const resultsDiv = document.getElementById('results');
    const audioFile = document.getElementById('audioFile');
    const uploadAudioButton = document.getElementById('uploadAudioButton');
    const audioResultsDiv = document.getElementById('audioResults');
    const saveFilenameInput = document.getElementById('saveFilename');
    const saveButton = document.getElementById('saveButton');
    const saveMessageDiv = document.getElementById('saveMessage');
    const fileListSelect = document.getElementById('fileList');
    const loadButton = document.getElementById('loadButton');
    const loadMessageDiv = document.getElementById('loadMessage');
    const fileContentDiv = document.getElementById('fileContent');
    const moduleListDiv = document.getElementById('moduleList');

    let availableModules = [];

    // Function to fetch and display available modules
    const fetchModules = async () => {
        try {
            const response = await fetch('/api/modules');
            const data = await response.json();
            if (data.modules) {
                availableModules = data.modules;
                renderModuleCheckboxes(availableModules);
            } else if (data.error) {
                console.error("Error fetching modules:", data.error);
            }
        } catch (error) {
            console.error("Failed to fetch modules:", error);
        }
    };

    // Function to render module selection checkboxes
    const renderModuleCheckboxes = (modules) => {
        moduleListDiv.innerHTML = '';
        modules.forEach(module => {
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = module;
            checkbox.value = module;
            checkbox.checked = true; // Default to all enabled

            const label = document.createElement('label');
            label.htmlFor = module;
            label.textContent = module;

            const div = document.createElement('div');
            div.appendChild(checkbox);
            div.appendChild(label);
            moduleListDiv.appendChild(div);
        });
    };

    // Event listener for processing text
    processButton.addEventListener('click', async () => {
        const text = inputText.value;
        const language = languageSelect.value;
        const selectedModules = Array.from(moduleListDiv.querySelectorAll('input[type="checkbox"]:checked'))
            .map(checkbox => checkbox.value);

        if (text) {
            resultsDiv.textContent = 'Processing...';
            try {
                const response = await fetch('/api/process', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ text, language, modules: selectedModules }),
                });
                const data = await response.json();
                resultsDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
            } catch (error) {
                resultsDiv.textContent = `Error: ${error.message}`;
            }
        } else {
            resultsDiv.textContent = 'Please enter some text to process.';
        }
    });

    // Enable upload button when a file is selected
    audioFile.addEventListener('change', () => {
        uploadAudioButton.disabled = !audioFile.files.length;
    });

    // Event listener for uploading audio
    uploadAudioButton.addEventListener('click', async () => {
        if (audioFile.files.length > 0) {
            audioResultsDiv.textContent = 'Uploading and processing audio...';
            const formData = new FormData();
            formData.append('file', audioFile.files[0]);
            formData.append('language', languageSelect.value); // Use the selected language

            try {
                const response = await fetch('/api/upload_audio', {
                    method: 'POST',
                    body: formData,
                });
                const data = await response.json();
                audioResultsDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
            } catch (error) {
                audioResultsDiv.textContent = `Error processing audio: ${error.message}`;
            }
        }
    });

    // Enable save button when filename is entered
    saveFilenameInput.addEventListener('input', () => {
        saveButton.disabled = !saveFilenameInput.value.trim();
    });

    // Event listener for saving text
    saveButton.addEventListener('click', async () => {
        const textToSave = inputText.value;
        const filename = saveFilenameInput.value.trim();

        if (textToSave && filename) {
            saveMessageDiv.textContent = 'Saving...';
            try {
                const response = await fetch('/api/save', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ text: textToSave, filename: filename }),
                });
                const data = await response.json();
                if (data.success) {
                    saveMessageDiv.textContent = `Saved to ${data.path}`;
                    fetchFileList(); // Refresh the file list after saving
                } else {
                    saveMessageDiv.textContent = `Error saving: ${data.error}`;
                }
            } catch (error) {
                saveMessageDiv.textContent = `Failed to save: ${error.message}`;
            }
        } else {
            saveMessageDiv.textContent = 'Please enter text and a filename to save.';
        }
    });

    // Function to fetch and populate the list of saved files
    const fetchFileList = async () => {
        try {
            const response = await fetch('/api/load');
            const data = await response.json();
            fileListSelect.innerHTML = '<option value="" disabled selected>Select a file to load</option>';
            if (data.files && data.files.length > 0) {
                data.files.forEach(file => {
                    const option = document.createElement('option');
                    option.value = file;
                    option.textContent = file;
                    fileListSelect.appendChild(option);
                });
                loadButton.disabled = false;
            } else {
                const option = document.createElement('option');
                option.value = "";
                option.textContent = "No files saved yet";
                fileListSelect.appendChild(option);
                loadButton.disabled = true;
            }
        } catch (error) {
            console.error("Error fetching file list:", error);
        }
    };

    // Event listener for loading a file
    loadButton.addEventListener('click', async () => {
        const selectedFile = fileListSelect.value;
        if (selectedFile) {
            loadMessageDiv.textContent = 'Loading...';
            try {
                const response = await fetch(`/api/load/${selectedFile}`);
                const data = await response.json();
                if (data.text) {
                    inputText.value = data.text;
                    fileContentDiv.innerHTML = `<pre>--- Loaded Content from ${selectedFile} ---\n${data.text}</pre>`;
                    loadMessageDiv.textContent = '';
                } else {
                    loadMessageDiv.textContent = `Error loading: ${data.error}`;
                    fileContentDiv.textContent = '';
                }
            } catch (error) {
                loadMessageDiv.textContent = `Failed to load: ${error.message}`;
                fileContentDiv.textContent = '';
            }
        } else {
            loadMessageDiv.textContent = 'Please select a file to load.';
        }
    });

    // Initialize by fetching the list of modules and saved files
    fetchModules();
    fetchFileList();
});