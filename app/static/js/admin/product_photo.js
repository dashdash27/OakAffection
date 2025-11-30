document.addEventListener('DOMContentLoaded', () => {
    const addPhotoBtn = document.getElementById('add-photo-btn');
    const photoEntries = document.querySelectorAll(".photo-entry");
    let photoCount = photoEntries.length;

    // добавляет обработчик на photoInput
    function setUpPhotoEntryHandlers(photoEntry) {
        const photoInput = photoEntry.querySelector(".photo-input");
        const errorMessage = photoEntry.querySelector(".error-message");
        const deletePhotoBtn = photoEntry.querySelector('.delete-photo-btn');

        deletePhotoBtn.addEventListener('click', () => {
            deletePhotoBtn.closest('.photo-entry').remove();
        })

        photoInput.addEventListener('change', function(event) {
            let input = event.target;
            let preview = photoEntry.querySelector('.preview-photo');

            if (input.files && input.files[0]) {
                let reader = new FileReader();
                reader.onload = function(e) {
                    preview.src = e.target.result; // Устанавливаем data URL загруженного файла
                    preview.style.display = 'block'; // Показываем изображение
                }
                reader.readAsDataURL(input.files[0]);
                
                if (isLatinFileName(input.files[0].name)) {
                    errorMessage.innerHTML = "";
                }
                else {
                    errorMessage.innerHTML = "Название файла может содержать только английские буквы, цифры и дефис";
                }

                photoInput.parentElement.querySelector('.custom-photo-name').innerHTML = input.files[0].name;
            } else {
                preview.src = '';
                preview.style.display = 'none'; // Если файл не выбран, скрываем превью
                errorMessage.innerHTML = "Не загружено фото";
                photoInput.parentElement.querySelector('.custom-photo-name').innerHTML = "-";
            }
        });
    }

    photoEntries.forEach((photoEntry) => {
        setUpPhotoEntryHandlers(photoEntry);
    })

    addPhotoBtn.addEventListener('click', () => {

        let container = document.getElementById('photos-list');
        let num = photoCount;

        let photoEntry = document.createElement('div');
        photoEntry.classList.add('photo-entry', 'media-entry');

        let newInput = document.createElement('input');
        newInput.type = 'file';
        newInput.name = 'photos-' + num + '-photo';
        newInput.id = 'photos-' + num + '-photo';
        newInput.accept = 'image/*';
        newInput.classList.add('photo-input', 'media-input');

        let newLabel = document.createElement('label');
        newLabel.setAttribute('for', newInput.id);
        newLabel.innerHTML = "Выбрать фото";
        newLabel.classList.add('custom-photo-input', 'custom-media-input');

        let photoName = document.createElement('div');
        photoName.classList.add('custom-photo-name', 'custom-media-name');

        const deletePhotoBtn = document.createElement('button');
        deletePhotoBtn.type = 'button';
        deletePhotoBtn.id = "delete-photo" + photoCount
        deletePhotoBtn.classList.add("delete-photo-btn");
        deletePhotoBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 14 14"><path fill="#e65c85" fill-rule="evenodd" d="M1.707.293A1 1 0 0 0 .293 1.707L5.586 7L.293 12.293a1 1 0 1 0 1.414 1.414L7 8.414l5.293 5.293a1 1 0 0 0 1.414-1.414L8.414 7l5.293-5.293A1 1 0 0 0 12.293.293L7 5.586z" clip-rule="evenodd"/></svg>'
        deletePhotoBtn.classList.add("delete-btn");

        let preview = document.createElement('img');
        preview.classList.add('preview-photo', 'preview-media');

        let errorMessage = document.createElement('div');
        errorMessage.classList.add('photo-error', 'media-error', 'error-message')
        errorMessage.innerHTML = "Не загружено фото";

        let photoAltWrapper = document.createElement('div');
        photoAltWrapper.classList.add("form-item");
        photoAltWrapper.style.width = "100%";
        let photoAltText = document.createElement('div');
        photoAltText.classList.add("form-text");
        photoAltText.innerHTML = "Описание картинки (~ 4-6 слов) <span>*</span>"
        let photoAltInput = document.createElement('input');
        photoAltInput.classList.add("form-input");
        photoAltInput.type = "text";
        photoAltInput.id = 'photos-' + num + '-alt';
        photoAltInput.name = 'photos-' + num + '-alt';
        photoAltInput.required = true;
        photoAltWrapper.appendChild(photoAltText);
        photoAltWrapper.appendChild(photoAltInput);


        photoEntry.appendChild(newInput);
        photoEntry.appendChild(newLabel);
        photoEntry.appendChild(photoName);
        photoEntry.appendChild(deletePhotoBtn);
        photoEntry.appendChild(preview);
        photoEntry.appendChild(errorMessage);
        photoEntry.appendChild(photoAltWrapper);

        container.appendChild(photoEntry);

        setUpPhotoEntryHandlers(photoEntry)

        photoCount += 1;
    });
});