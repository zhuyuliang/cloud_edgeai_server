/**
 * 提示框
 * @param text
 * @param icon
 * @param hideAfter

  myAlert("成功样式！", "success", 2000);
  myAlert("提示样式！", "info", 2000);
  myAlert("警告样式！", "warning", 2000);
  myAlert("错误样式！", "error", 2000);
 */

// 动态添加自定义提示框CSS样式
if (!document.getElementById('xc-alert-styles')) {
    const style = document.createElement('style');
    style.id = 'xc-alert-styles';
    style.textContent = `
        /* 自定义提示框样式 */
        .xc-alert {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            padding: 16px 24px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            color: white;
            z-index: 99999 !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            animation: xcAlertSlideIn 0.3s ease-out;
            display: flex;
            align-items: center;
            gap: 10px;
            max-width: 90%;
            word-wrap: break-word;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .xc-alert.success {
            background-color: #4CAF50;
            border-left: 4px solid #388E3C;
        }
        
        .xc-alert.error {
            background-color: #F44336;
            border-left: 4px solid #D32F2F;
        }
        
        .xc-alert.info {
            background-color: #2196F3;
            border-left: 4px solid #1976D2;
        }
        
        .xc-alert.warning {
            background-color: #FF9800;
            border-left: 4px solid #F57C00;
        }
        
        @keyframes xcAlertSlideIn {
            from {
                opacity: 0;
                transform: translateX(-50%) translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(-50%) translateY(0);
            }
        }
        
        @keyframes xcAlertSlideOut {
            from {
                opacity: 1;
                transform: translateX(-50%) translateY(0);
            }
            to {
                opacity: 0;
                transform: translateX(-50%) translateY(-20px);
            }
        }
        
        .xc-alert.fade-out {
            animation: xcAlertSlideOut 0.3s ease-in forwards;
        }
        
        .xc-alert-icon {
            font-size: 20px;
        }
        
        .xc-alert-close {
            background: none;
            border: none;
            color: white;
            font-size: 16px;
            cursor: pointer;
            margin-left: 10px;
            opacity: 0.8;
            transition: opacity 0.2s;
        }
        
        .xc-alert-close:hover {
            opacity: 1;
        }
    `;
    document.head.appendChild(style);
}

// 自定义提示框函数
function xcAlert(text, icon = 'info', hideAfter = 2000) {
    // 移除现有的提示框
    const existingAlerts = document.querySelectorAll('.xc-alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // 创建提示框元素
    const alertElement = document.createElement('div');
    alertElement.className = `xc-alert ${icon}`;
    
    // 添加图标
    let iconHTML = '';
    switch(icon) {
        case 'success':
            iconHTML = '<span class="xc-alert-icon">✓</span>';
            break;
        case 'error':
            iconHTML = '<span class="xc-alert-icon">✗</span>';
            break;
        case 'info':
            iconHTML = '<span class="xc-alert-icon">ℹ</span>';
            break;
        case 'warning':
            iconHTML = '<span class="xc-alert-icon">⚠</span>';
            break;
        default:
            iconHTML = '<span class="xc-alert-icon">ℹ</span>';
            break;
    }
    
    // 设置提示框内容
    alertElement.innerHTML = `
        ${iconHTML}
        <span class="xc-alert-text">${text}</span>
        <button class="xc-alert-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    
    // 添加到页面
    document.body.appendChild(alertElement);
    
    // 设置自动关闭
    if (hideAfter > 0) {
        setTimeout(() => {
            alertElement.classList.add('fade-out');
            setTimeout(() => {
                if (alertElement.parentNode) {
                    alertElement.remove();
                }
            }, 300);
        }, hideAfter);
    }
}

// 重写myAlert函数，使用自定义提示框
function myAlert(text, icon = 'info', hideAfter = 2000) {
    xcAlert(text, icon, hideAfter);
}