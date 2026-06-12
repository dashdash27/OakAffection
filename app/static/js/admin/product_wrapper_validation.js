document.addEventListener('DOMContentLoaded', () => {
    // Input length
    const inputLength = document.querySelector(".input-length");
    inputLength.addEventListener('input', () => {
        let value = inputLength.value;
        value = value.replace(/\D/g, '');
        value = value.replace(/^0+/, '');
        inputLength.value = value;
    })

    // Input depth
    const inputDepth = document.querySelector(".input-depth");
    inputDepth.addEventListener('input', () => {
        let value = inputDepth.value;
        value = value.replace(/\D/g, '');
        value = value.replace(/^0+/, '');
        inputDepth.value = value;
    })

    // Input height
    const inputHeight = document.querySelector(".input-height");
    inputHeight.addEventListener('input', () => {
        let value = inputHeight.value;
        value = value.replace(/\D/g, '');
        value = value.replace(/^0+/, '');
        inputHeight.value = value;
    })
});
