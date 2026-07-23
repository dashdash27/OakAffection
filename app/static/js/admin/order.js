document.addEventListener('DOMContentLoaded', () => {
    const orderId = document.querySelector('.order-detail').getAttribute('data-order-id');
    
    // 1. Action Buttons
    const actionButtons = document.querySelectorAll('.action-btn');
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    actionButtons.forEach(button => {
        button.addEventListener('click', async (e) => {
            const action = button.getAttribute('data-action');

            const result = await fetchChangeOrderStatus(orderId, action);

            if (result.success) {
                showToastAfterReload("Статус заказа успешно обновлен", "success");
                location.reload();
            } else {
                showToast("Не удалось изменить статус заказа. Попробуйте еще раз", "error");
            }

        });
    });

    async function fetchChangeOrderStatus(orderId, action) {
        try {
            const response = await fetch(`/admin/orders/${orderId}/action`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ action: action })
            })

            if (response.ok) {
                const data = await response.json();
                return { success: true, data: data };
            }
            
            const errorData = await response.json().catch(() => ({}));
            return { 
                success: false, 
                message: errorData.error || "Ошибка сервера при изменении статуса заказа" 
            };
        } catch (error) {
            return { success: false, message: "Проблема с сетью: " + error.message };
        }
    }

    // 2. Track Number
    const trackInput = document.querySelector('.track-input');
    const trackBtn = document.querySelector('.track-btn');

    trackBtn.addEventListener('click', async (e) => {
        if (trackInput.disabled) {
            trackInput.disabled = false; // Разблокируем поле для ввода
            trackInput.focus();          // Ставим курсор внутрь
            trackBtn.innerText = "Сохранить и отправить клиенту";
            trackBtn.style.background = "var(--accent-color)";
            trackBtn.style.color = "#ffffff";
            trackBtn.style.borderColor = "#b7eb8f";
            return;
        }

        const deliveryTrack = trackInput.value.trim();
        if (!deliveryTrack) {
            alert("Введите трек-номер!");
            return;
        }

        // Вызываем fetch
        const result = await fetchSaveOrderTrack(orderId, deliveryTrack);

        if (result.success) {
            showToastAfterReload("Трек номер успешно сохранен и отправлен клиенту", "success");
            location.reload();
        } else {
            showToast("Не удалось сохранить и отправить трек-номер. Попробуйте еще раз", "error");
        }

    });

    async function fetchSaveOrderTrack(orderId, deliveryTrack) {
        try {
            const response = await fetch(`/admin/orders/${orderId}/track`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ delivery_track: deliveryTrack })
            })

            if (response.ok) {
                const data = await response.json();
                return { success: true, data: data };
            }
            
            const errorData = await response.json().catch(() => ({}));
            return { 
                success: false, 
                message: errorData.error || "Ошибка сервера при отправке и сохранении трек-номера" 
            };
        } catch (error) {
            return { success: false, message: "Проблема с сетью: " + error.message };
        }
    }

    // Comment 
    const commentInput = document.querySelector('.order-comment-input');
    const commentBtn = document.querySelector('.save-comment-btn');

    commentBtn.addEventListener('click', async (e) => {
        const commentText = commentInput.value.trim();

        const result = await fetchSaveOrderComment(orderId, commentText);

        if (result.success) {
            showToastAfterReload("Комментарий к заказу успешно обновлен", "success");
            location.reload();
        } else {
            showToast("Не удалось сохранить комментарий. Попробуйте еще раз", "error");
        }

    });

    async function fetchSaveOrderComment(orderId, commentText) {
        try {
            const response = await fetch(`/admin/orders/${orderId}/comment`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ comment_text: commentText })
            })

            if (response.ok) {
                const data = await response.json();
                return { success: true, data: data };
            }
            
            const errorData = await response.json().catch(() => ({}));
            return { 
                success: false, 
                message: errorData.error || "Ошибка сервера при изменении комментария к заказу" 
            };
        } catch (error) {
            return { success: false, message: "Проблема с сетью: " + error.message };
        }
    }

    /* Toasts */
    function showToast(message, type = 'success') {
        const toastContainer = document.querySelector('.toast-container');
        
        const toast = document.createElement('div');
        toast.className = `toast-item toast-${type}`;
        toast.innerHTML = `<span>${message}</span>`;

        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('fade-out');
            setTimeout(() => {
                toast.remove();
            }, 250);
        }, 3000);
    }

    function showToastAfterReload(message, type = 'success') {
        sessionStorage.setItem('pendingToast', JSON.stringify({ message, type }));
    }

    const pendingToast = sessionStorage.getItem('pendingToast');
    if (pendingToast) {
        const toastData = JSON.parse(pendingToast);
        showToast(toastData.message, toastData.type);
        sessionStorage.removeItem('pendingToast'); 
    }

});