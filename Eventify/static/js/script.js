// 这里将添加前端JavaScript代码
console.log('网站已加载');

document.addEventListener('DOMContentLoaded', () => {
    // Flash message dismissal
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(message => {
        const closeBtn = message.querySelector('.close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                message.style.display = 'none';
            });
        }
    });

    // Form submission handling
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            fetch(form.action, {
                method: form.method,
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('success', data.message);
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    }
                } else {
                    showAlert('danger', data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('danger', 'An error occurred. Please try again.');
            });
        });
    });

    // Helper function to show alerts
    function showAlert(type, message) {
        const modalHtml = `
            <div class="modal fade" id="alertModal" tabindex="-1" role="dialog" aria-labelledby="alertModalLabel" aria-hidden="true">
                <div class="modal-dialog" role="document">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="alertModalLabel">${type === 'success' ? 'Success' : 'Error'}</h5>
                            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                                <span aria-hidden="true">&times;</span>
                            </button>
                        </div>
                        <div class="modal-body">
                            ${message}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 移除任何现有的模态框
        const existingModal = document.getElementById('alertModal');
        if (existingModal) {
            existingModal.remove();
        }

        // 添加新的模态框到 body
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // 显示模态框
        $('#alertModal').modal('show');
    }

    // Data fetching for activities or other dynamic content
    const dataList = document.getElementById('data-list');
    if (dataList) {
        fetch('/api/data')
            .then(response => response.json())
            .then(data => {
                data.forEach(item => {
                    const li = document.createElement('li');
                    li.textContent = `${item.name}: ${item.value}`;
                    dataList.appendChild(li);
                });
            });
    }

    // 流星效果
    function createShootingStar() {
        const star = document.createElement('div');
        star.className = 'shooting-star';
        
        // 随机位置（在屏幕顶部15%的区域内）
        const top = Math.random() * (window.innerHeight * 0.15);
        const left = Math.random() * window.innerWidth;
        
        star.style.top = `${top}px`;
        star.style.left = `${left}px`;
        
        // 随机角度（30-60度）
        const angle = Math.random() * 30 + 30;
        
        // 设置动画
        star.style.transform = `rotate(${angle}deg)`;
        
        document.body.appendChild(star);
        
        // 动画结束后移除流星
        setTimeout(() => {
            star.remove();
        }, 3000);
    }

    function shootingStarEffect() {
        setInterval(createShootingStar, 2000); // 每2秒创建一个新的流星
    }

    shootingStarEffect(); // 启动流星效果
});
