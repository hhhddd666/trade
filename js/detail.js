var vm = new Vue({
    el: '#app',
    // 修改Vue变量的读取语法，避免和django模板语法冲突
    delimiters: ['[[', ']]'],
    data: {
        host,
        show_menu:false,
        data_config:'{"skin": "moono-lisa", "toolbar_Basic": [["Source", "-", "Bold", "Italic"]], "toolbar_Full": [["Styles", "Format", "Bold", "Italic", "Underline", "Strike", "SpellChecker", "Undo", "Redo"], ["Link", "Unlink", "Anchor"], ["Image", "Flash", "Table", "HorizontalRule"], ["TextColor", "BGColor"], ["Smiley", "SpecialChar"], ["Source"]], "toolbar": "Custom", "height": "250px", "width": "auto", "filebrowserWindowWidth": 940, "filebrowserWindowHeight": 725, "tabSpaces": 4, "toolbar_Custom": [["Smiley", "CodeSnippet"], ["Bold", "Italic", "Underline", "RemoveFormat", "Blockquote"], ["TextColor", "BGColor"], ["Link", "Unlink"], ["NumberedList", "BulletedList"], ["Maximize"]], "extraPlugins": "codesnippet,prism,widget,lineutils", "language": "en-us"}',
        username:'',
        is_login:false,
    },
    mounted(){
        this.username=getCookie('username');
        this.is_login=getCookie('is_login');
    },
    methods: {
        //显示下拉菜单
        show_menu_click:function(){
            this.show_menu = !this.show_menu ;
        },
    }
});
// detail.js - 改进聊天功能
let currentReceiverId = null;
let currentPropertyId = null;

function openChat(agentName, agentPhone, receiverId, propertyId) {
    currentReceiverId = receiverId;
    currentPropertyId = propertyId;

    $('#chatWindow').modal('show');

    // 加载历史消息
    loadChatHistory();

    // 设置定时器自动刷新消息
    setInterval(loadChatHistory, 5000); // 每5秒刷新一次
}

function loadChatHistory() {
    if (!currentReceiverId) return;

    fetch(`/chat/messages/?receiver_id=${currentReceiverId}&property_id=${currentPropertyId}`)
        .then(response => response.json())
        .then(data => {
            const chatDiv = document.getElementById('chatMessages');
            chatDiv.innerHTML = ''; // 清空现有消息

            data.messages.forEach(msg => {
                const messageDiv = document.createElement('div');
                messageDiv.className = msg.is_current_user ? 'user-message text-right mb-2' : 'agent-message mb-2';

                const badgeClass = msg.is_current_user ? 'badge-primary' : 'badge-success';
                messageDiv.innerHTML = `
                    <div class="d-flex ${msg.is_current_user ? 'justify-content-end' : 'justify-content-start'}">
                        <span class="badge ${badgeClass}">
                            ${msg.sender}: ${msg.message}
                        </span>
                    </div>
                    <small class="text-muted d-block">${msg.timestamp}</small>
                `;
                chatDiv.appendChild(messageDiv);
            });

            // 滚动到底部
            chatDiv.scrollTop = chatDiv.scrollHeight;
        })
        .catch(error => console.error('加载消息失败:', error));
}

function sendMessage() {
    const message = document.getElementById('messageInput').value.trim();
    if (message === '' || !currentReceiverId) return;

    // 发送消息到服务器
    fetch('/chat/send/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')  // 获取CSRF token
        },
        body: JSON.stringify({
            receiver_id: currentReceiverId,
            message: message,
            property_id: currentPropertyId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('messageInput').value = '';
            loadChatHistory(); // 重新加载消息
        } else {
            alert('发送失败: ' + data.error);
        }
    })
    .catch(error => {
        console.error('发送消息失败:', error);
        alert('发送失败，请重试');
    });
}

// 获取CSRF token的辅助函数
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
