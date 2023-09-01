window.addEventListener('load', function() {
    setTimeout(function() {
        var preloader = document.querySelector('.preloader');

        preloader.style.opacity = 0;
    }, 500);

    setTimeout(function() {
        var preloader = document.querySelector('.preloader');

        preloader.style.display = 'none';
    }, 1000);
});

var content_header = document.querySelector('.app-content-headerText');
var items_header = document.querySelector('.items-header');
var items = document.querySelector('.items-table');
var account_name = document.querySelector('.account-info-name');
var account_image = document.querySelector('.account-info-image');

eel.expose(set_interface);
function set_interface(info, is_playing) {
    if (!is_playing) {
        content_header.innerHTML = 'Levels';

        items_header.innerHTML = '<div class="item-cell">Name</div>' +
                         '<div class="item-cell">Difficulty</div>' +
                         '<div class="item-cell">ID</div>' +
                         '<div class="item-cell">Players</div>';

        levels = '';

        info['rooms'].forEach(function(room) {
            levels += '<div class="items-row">' +
                      '<div class="item-cell">' +
                      room['level_name'] +
                      '</div>' +
                      '<div class="item-cell">' +
                      '<img src="./images/' + room['level_difficulty'] + '.png">' +
                      '</div>' +
                      '<div class="item-cell">' +
                      room['name'] +
                      '</div>' +
                      '<div class="item-cell">' +
                      room['nb_players'] + '/' + room['capacity'] +
                      '</div>' +
                      '</div>';
        });

        items.innerHTML = levels;
    }

    else {
        content_header.innerHTML = 'Level: ' + info['level_name'] +
                                   '<br>Difficulty: ' + info['level_difficulty'] +
                                   '<img src="./images/' + info['level_difficulty'] + '.png">' +
                                   '<br>ID: ' + info['level_id'] +
                                   '<br>Players: ' + (Object.keys(info['players']).length + 1) + '/' + info['capacity'];

        items_header.innerHTML = '<div class="item-cell">Player</div>' +
                                 '<div class="item-cell">Progress</div>';

        players = '';

        Object.keys(info['players']).forEach(function(player) {
            players += '<div class="items-row">' +
                       '<div class="item-cell">';

            if (info['players'][player][0] != 'Downloading icons...')
               players += '<img src="' + info['players'][player][2] + '">';

            players += player +
                       '</div>' +
                       '<div class="item-cell">';

            if (info['players'][player][0] == 'Downloading icons...')
                players += 'Downloading icons...';

            else {
                players += '<div class="progress-container">' +
                           '<div class="progress">' +
                           '<div class="progress-bar';

                percent = info['players'][player][0].slice(0, -1);

                if (percent <= 25)
                    players += ' low" ';

                else if (percent <= 50)
                    players += ' middle" ';

                else if (percent <= 75)
                    players += ' high" ';

                players += 'style="width: ' +
                            info['players'][player][0].slice(0, -1) +
                            '%;"></div>' +
                            '</div>' +
                            '</div>' +
                            info['players'][player][0] +
                            (info['players'][player][1] - 0 ? ' Died!' : '');
           }

           players += '</div>' +
                      '</div>';
        });

        items.innerHTML = players;
    }
}

eel.expose(set_account_info);
function set_account_info(acc_name, player_icon) {
    account_name.innerHTML = acc_name;
    account_image.innerHTML = '<img src="' + player_icon + '">';
}

eel.expose(call_alert);
function call_alert(status, title, content, code=0, confirmbtn=false) {
    SuperAlert.alert({
        status: status,
        title: title,
        content: content,
        code: code,
        confirmbtn: confirmbtn
    });
}

window.onresize = function() {
    if (window.innerWidth > 1280)
        window.resizeTo(1280, 800);
};