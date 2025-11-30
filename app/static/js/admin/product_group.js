updateGroups();

function updateGroups() {
    const groupSelect = document.querySelector(".group-select");
    const charsList = document.querySelector(".characteristics-list");
    const charItems = charsList.querySelectorAll(".characteristic-item");

    // получаем id всех характеристик, которые выбраны у продукта
    const charIdsSet = new Set();
    charItems.forEach(charItem => {
        const value = charItem.querySelector('select').value;
        charIdsSet.add(value);
    });

    groupOptions = groupSelect.querySelectorAll('option');
    groupOptions.forEach(option => {
        if (option.value != 0) {
            if (!charIdsSet.has(option.getAttribute('data-characteristic-id'))) {
                option.disabled = true;
            }
            else {
                option.disabled = false;
            }
        }
    });

    // проверка, если удалили характеристику, нужно сбросить и группу
    const options = Array.from(groupSelect.options);
    const isSelectedActive = options.some(opt => !opt.disabled && opt.value === groupSelect.value);
    const groupError = document.querySelector('.group-error');
    if (!isSelectedActive) {
        groupSelect.value = "0"; 
        groupError.innerHTML = 'Характристика группы была удалена, поэтому установленная группа была сброшена';
    }
}