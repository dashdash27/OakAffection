const addCharBtn = document.getElementById('add-characteristic');
const deleteCharBtns = document.querySelectorAll('.delete-characteristic');
const characteristicsList = document.querySelector('.characteristics-list');
const characteristicTemplate = document.querySelector('.characteristic-template').querySelector('.characteristic-item');
let counter = characteristicsList.querySelectorAll(".characteristic-item").length;

characteristicsList.addEventListener('click', (event) => {
    if (event.target.classList.contains('delete-characteristic')) {
        const itemToDelete = event.target.closest('.characteristic-item');
        if (itemToDelete) {
            itemToDelete.remove();
            updateGroups();
        }
    }
});

addCharBtn.addEventListener('click', () => {
    // Дублируем шаблон характеристики в characteristicsList
    const newItem = characteristicTemplate.cloneNode(true);

    // Обновить имена и id чтобы Flask-WTF их корректно распознал
    newItem.querySelectorAll('input').forEach((input) => {
        input.name = "characteristics-" + counter + "-value";
        input.id = "characteristics-" + counter + "-value";
        input.value = '';
        input.disabled = false;
        input.required = true;
    });
    newItem.querySelectorAll('select').forEach((select) => {
        select.name = "characteristics-" + counter + "-characteristic_id";
        select.id = "characteristics-" + counter + "-characteristic_id";
        select.disabled = false;
        select.required = true;
    });

    // обработчик на изменение
    newItem.querySelector('select').addEventListener('change', () => {
        updateGroups();
    });

    characteristicsList.appendChild(newItem);
    updateGroups();
    counter += 1;
});
