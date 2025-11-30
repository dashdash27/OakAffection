// Create select for categories
const multipleCancelButton1 = new Choices('.categories-select', {
    searchEnabled: false,
    removeItemButton: true,
    removeItemIconText: '×',
    maxItemCount: -1
});

// Найти контейнер выбранных элементов
const selectedItems1 = document.querySelector('.categories').querySelector('.choices__list--multiple');

// Создать и вставить кастомный разделитель
const separator1 = document.createElement('div');
separator1.textContent = 'Категории (нажмите, чтобы выбрать)';
separator1.classList.add("form-text");

selectedItems1.parentNode.insertBefore(separator1, selectedItems1.nextSibling);

const multipleCancelButton2 = new Choices('.targets-select', {
    searchEnabled: false,
    removeItemButton: true,
    removeItemIconText: '×',
    maxItemCount: -1
});

// Найти контейнер выбранных элементов
const selectedItems2 = document.querySelector('.targets').querySelector('.choices__list--multiple');

// Создать и вставить кастомный разделитель
const separator2 = document.createElement('div');
separator2.textContent = 'Элементы (нажмите, чтобы выбрать)';
separator2.classList.add("form-text");

selectedItems2.parentNode.insertBefore(separator2, selectedItems2.nextSibling);
