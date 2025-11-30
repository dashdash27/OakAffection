document.addEventListener('DOMContentLoaded', () => {
    const addVideoBtn = document.getElementById('add-video-btn');
    const videoEntries = document.querySelectorAll(".video-entry");
    let videoCount = videoEntries.length + 2;

    addVideoBtn.addEventListener('click', () => {
        let container = document.getElementById('videos-list');
        let num = videoCount;

        let videoEntry = document.createElement('div');
        videoEntry.classList.add('video-entry', 'media-entry');

        let newInput = document.createElement('input');
        newInput.type = 'file';
        newInput.name = 'videos-' + num + '-video';
        newInput.id = 'videos-' + num + '-video';
        newInput.accept = 'video/*';
        newInput.classList.add('video-input', 'media-input');

        let newLabel = document.createElement('label');
        newLabel.setAttribute('for', newInput.id);
        newLabel.innerHTML = "Выбрать видео";
        newLabel.classList.add('custom-video-input', 'custom-media-input');

        let videoName = document.createElement('div');
        videoName.classList.add('custom-video-name', 'custom-media-name');

        const deleteVideoBtn = document.createElement('button');
        deleteVideoBtn.type = 'button';
        deleteVideoBtn.id = "delete-video" + videoCount;
        deleteVideoBtn.classList.add("delete-video-btn", "delete-btn");
        deleteVideoBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 14 14"><path fill="#e65c85" fill-rule="evenodd" d="M1.707.293A1 1 0 0 0 .293 1.707L5.586 7L.293 12.293a1 1 0 1 0 1.414 1.414L7 8.414l5.293 5.293a1 1 0 0 0 1.414-1.414L8.414 7l5.293-5.293A1 1 0 0 0 12.293.293L7 5.586z" clip-rule="evenodd"/></svg>';

        let preview = document.createElement('video');
        preview.classList.add('preview-video', 'preview-media');
        preview.style.display = 'none';
        preview.controls = true;

        let errorMessage = document.createElement('div');
        errorMessage.classList.add('video-error', 'media-error', 'error-message')
        errorMessage.innerHTML = "Не загружено видео";

        videoEntry.appendChild(newInput);
        videoEntry.appendChild(newLabel);
        videoEntry.appendChild(videoName);
        videoEntry.appendChild(deleteVideoBtn);
        videoEntry.appendChild(preview);
        videoEntry.appendChild(errorMessage);

        container.appendChild(videoEntry);

        setUpVideoEntryHandlers(videoEntry);

        videoCount += 1;
    });

    function setUpVideoEntryHandlers(videoEntry) {
        // Своя переменная currentVideoURL для каждого блока
        videoEntry.currentVideoURL = null;

        const videoInput = videoEntry.querySelector(".video-input");
        const errorMessage = videoEntry.querySelector(".error-message");
        const deleteVideoBtn = videoEntry.querySelector('.delete-video-btn');
        const preview = videoEntry.querySelector('.preview-video');
        const videoName = videoEntry.querySelector('.custom-video-name');

        deleteVideoBtn.addEventListener('click', () => {
            if (videoEntry.currentVideoURL) {
                URL.revokeObjectURL(videoEntry.currentVideoURL);
            }
            videoEntry.remove();
        });

        videoInput.addEventListener('change', (event) => {
            if (videoEntry.currentVideoURL) {
                URL.revokeObjectURL(videoEntry.currentVideoURL);
            }

            if (videoInput.files && videoInput.files[0]) {
                const file = videoInput.files[0];
                const videoURL = URL.createObjectURL(file);

                videoEntry.currentVideoURL = videoURL;
                preview.src = videoURL;
                preview.style.display = 'block';

                // Проверка имени файла латиницей
                if (isLatinFileName(file.name)) {
                    errorMessage.innerHTML = "";
                } else {
                    errorMessage.innerHTML = "Название файла может содержать только английские буквы, цифры и дефис";
                }

                videoName.innerHTML = file.name;
            } else {
                preview.src = "";
                preview.style.display = 'none';
                errorMessage.innerHTML = "Не загружено видео";
                videoName.innerHTML = "-";
                videoEntry.currentVideoURL = null;
            }
        });
    }

    // Инициализация обработчиков для уже существующих видео блоков
    videoEntries.forEach((videoEntry) => {
        setUpVideoEntryHandlers(videoEntry);
    });
});
