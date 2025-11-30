function isLatinFileName(fileName) {
    return /^[a-zA-Z0-9_\-\.]+$/.test(fileName);
}