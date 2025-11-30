// проверка уникальных характеристиик
function checkUniqueChracteristics() {
    const selects = characteristicsList.querySelectorAll('select');
    const values = Array.from(selects).map(select => select.value);
    const uniqueValues = new Set(values);

    if (uniqueValues.size !== values.length) {
        return false
    } else {
        return true
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form');
    const allErrors = document.querySelector('.all-errors');

    // Ввод цены
    const inputPrice = document.querySelector(".input-price");
    inputPrice.addEventListener('input', () => {
        let value = inputPrice.value;
        // удаляем все нецифры и ведущие нули
        value = value.replace(/\D/g, '');
        value = value.replace(/^0+/, '');

        inputPrice.value = value;
    })

    form.addEventListener('submit', function(event) {
        let valid = true;

        // Название
        const inputName = document.querySelector(".input-name");
        const nameError = document.querySelector(".name-error");
        if (inputName.value.trim() === '') {
            valid = false;
            nameError.innerHTML = "Поле не должно быть пустым";
        } else {
            nameError.innerHTML = "";
        }

        // Мини-описание
        const inputDescriptionTag = document.querySelector(".input-description-tag");
        const descriptionTagError = document.querySelector(".description-tag-error");
        if (inputDescriptionTag.value.trim() === '') {
            valid = false;
            descriptionTagError.innerHTML = "Поле не должно быть пустым";
        } else {
            descriptionTagError.innerHTML = "";
        }

        // Цена (потом откроем)
        // const inputPrice = document.querySelector(".input-price");
        // const priceError = document.querySelector(".price-error");
        // if (inputPrice.value.trim() === '') {
        //     valid = false;
        //     priceError.innerHTML = "Поле не должно быть пустым";
        // } else {
        //     priceError.innerHTML = "";
        // }

        // Characteristics
        const charsError = document.querySelector(".characteristics-error");
        // -- check dupel
        if (!checkUniqueChracteristics()) {
            charsError.innerHTML = "Характеристики не могут дублироваться";
            valid = false;
        }
        else {
            charsError.innerHTML = ""
        }

        // Cetegories
        const categoriesSelect = document.querySelector(".categories-select");
        const categoriesError = document.querySelector(".categories-error");
        if (categoriesSelect.selectedOptions.length == 0) {
            categoriesError.innerHTML = "Нужно выбрать хотя бы одну категорию";
            valid = false;
        }
        else {
            categoriesError.innerHTML = "";
        }

        // Media
        const mediaErrors = document.querySelectorAll(".media-error");
        mediaErrors.forEach(mediaError => {
            if (mediaError.innerHTML != '') 
                valid = false;
        })


        // Отменяем отправку
        if (!valid) {
            event.preventDefault();
            allErrors.innerHTML = "Некоторые поля заполнены некорректно, исправьте их, пожалуйста."
        }
    });
});
