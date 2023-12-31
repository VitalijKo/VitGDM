window.onload = () => {
    setTimeout(() => {
        const preloader = document.querySelector('.preloader');

        preloader.style.opacity = 0;
    }, 500);

    setTimeout(() => {
        const preloader = document.querySelector('.preloader');

        preloader.style.display = 'none';
    }, 1000);
};

window.onresize = () => {
    if (window.innerWidth > 700) window.resizeTo(700, 800);
};

save.onclick = (e) => {
    const server = document.querySelector('#server');
    const fps = document.querySelector('#fps');
    const display_icons = document.querySelector('#icons');
    const settings = {
        'SERVER': server.value,
        'FPS': fps.value,
        'ICONS': display_icons.checked
    };

    if (fps.value < 30 || fps.value > 360) {
        SuperAlert.alert({
            status: 'error',
            title: 'Error',
            content: '',
            code: 0,
            confirmbtn: false
        });
    }

    else eel.change_settings(settings);
};

check_update.onclick = () => eel.check_update();
open_ports.onclick = () => eel.open_ports();

var save = document.querySelector('#save');
var check_update = document.querySelector('#check-update');
var open_ports = document.querySelector('#open-ports');
var account_name = document.querySelector('.account-info-name');
var account_image = document.querySelector('.account-info-image');
var content_header = document.querySelector('.app-content-headerText');

eel.get_settings()((settings) => {
    const server = document.querySelector('#server');
    const fps = document.querySelector('#fps');
    const display_icons = document.querySelector('#icons');

    server.value = settings['SERVER'];
    fps.value = settings['FPS'];
    display_icons.checked = settings['ICONS'];
});

eel.expose(set_interface);

function set_interface(info, is_playing) {}

eel.expose(set_account_info);

function set_account_info(acc_name, player_icon) {
    account_name.innerHTML = acc_name;
    account_image.innerHTML = '<img src="' + player_icon + '">';
}

eel.expose(call_alert);

function call_alert(status, title, content, code = 0, confirmbtn = false) {
    SuperAlert.alert({
        status: status,
        title: title,
        content: content,
        code: code,
        confirmbtn: confirmbtn
    });
}
