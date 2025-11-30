const videos = document.querySelectorAll('.video');
const playPauseBtns = document.querySelectorAll('.play-pause-btn');
const muteBtns = document.querySelectorAll('.mute-btn');

const swiper = new Swiper('.swiper', {
    lazy: true,
    loadPrevNext: true,
    watchSlidesProgress: true,
    watchSlidesVisibility: true,
    navigation: {
        nextEl: '.swiper-button-next',
        prevEl: '.swiper-button-prev',
    },
    pagination: {
        el: '.swiper-pagination',
        clickable: true,
    },
    loop: false,
});

playPauseBtns.forEach((playPauseBtn, index) => {
    playPauseBtn.addEventListener('click', () => {
        if (videos[index].paused) {
            videos[index].play();
            playPauseBtn.innerHTML = `<img src="/static/img/icons/pause.svg" alt="">`;
        } 
        else {
            videos[index].pause();
            playPauseBtn.innerHTML = `<img src="/static/img/icons/play.svg" alt="">`;
        }
    });
});

// Обработчик для кнопки mute/unmute
muteBtns.forEach((muteBtn, index) => {
    muteBtn.addEventListener('click', () => {
        videos[index].muted = !videos[index].muted;
        // Меняем иконку в зависимости от состояния
        if (videos[index].muted) {
            muteBtn.innerHTML = `<img src="/static/img/icons/mute.svg" alt="">`;
        } else {
            muteBtn.innerHTML = `<img src="/static/img/icons/sound.svg" alt="">`;
        }
    });
});

function muteAllVideos() {
    muteBtns.forEach((muteBtn, index) => {
        videos[index].muted = true;
        muteBtn.innerHTML = `<img src="/static/img/icons/mute.svg" alt="">`;
    });
}

swiper.on('slideChange', () => {
    const videos = document.querySelectorAll('.video');
    muteAllVideos()
});
