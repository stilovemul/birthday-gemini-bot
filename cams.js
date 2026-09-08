(function () {
    'use strict';

    if (window.appready) {
        initPlugin();
    } else {
        Lampa.Listener.follow('app', function (e) {
            if (e.type == 'ready') initPlugin();
        });
    }

    function initPlugin() {
        var items = [
            {
                title: 'Санкт-Петербург: Дворцовая площадь',
                video: 'https://camera.piter.tv/live/dvortsovaya.m3u8',
                icon: 'https://img.freepik.com/free-photo/saint-petersburg_1157-1234.jpg'
            },
            {
                title: 'Санкт-Петербург: Невский проспект',
                video: 'https://camera.piter.tv/live/nevsky.m3u8'
            },
            {
                title: 'Санкт-Петербург: Лахта Центр (Панорама)',
                video: 'https://camera.piter.tv/live/lahta.m3u8'
            },
            {
                title: 'Телеканал Санкт-Петербург HD',
                video: 'http://sewv654wfcsdwfi87fwvgbngh.siauliairsavlt.pw/iptv/LNUZFZ7YFN4ACA/715/index.m3u8'
            },
            {
                title: 'Мир Белогорья HD (Белгород)',
                video: 'http://sewv654wfcsdwfi87fwvgbngh.siauliairsavlt.pw/iptv/LNUZFZ7YFN4ACA/20126/index.m3u8'
            },
            {
                title: 'Якутия 24 (Нерюнгри / Саха)',
                video: 'http://sewv654wfcsdwfi87fwvgbngh.siauliairsavlt.pw/iptv/LNUZFZ7YFN4ACA/20015/index.m3u8'
            },
            {
                title: 'НВК Саха HD (Нерюнгри / Якутия)',
                video: 'http://sewv654wfcsdwfi87fwvgbngh.siauliairsavlt.pw/iptv/LNUZFZ7YFN4ACA/20125/index.m3u8'
            }
        ];

        function createButton() {
            var btn = $('<li class="menu__item selector" data-action="city_cams"><div class="menu__ico"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg></div><div class="menu__text">Камеры городов</div></li>');
            btn.on('hover:enter', function () {
                Lampa.Component.add('city_cams', function () {
                    var comp = new Lampa.InteractionMain();
                    comp.create = function () {
                        this.activity.loader(false);
                        var scroll = new Lampa.Scroll({mask: true, over: true});
                        var body = $('<div class="category-full"></div>');
                        items.forEach(function (elem) {
                            var card = $('<div class="card-cam selector" style="padding: 16px; margin: 8px; background: rgba(255,255,255,0.1); border-radius: 8px; font-size: 1.2em; cursor: pointer;">' + elem.title + '</div>');
                            card.on('hover:enter', function () {
                                Lampa.Player.play({
                                    title: elem.title,
                                    url: elem.video
                                });
                            });
                            body.append(card);
                        });
                        scroll.append(body);
                        return scroll.render();
                    };
                    return comp;
                });
                Lampa.Activity.push({
                    url: '',
                    title: 'Камеры городов: СПб, Белгород, Нерюнгри',
                    component: 'city_cams',
                    page: 1
                });
            });
            $('.menu .menu__list').append(btn);
        }

        createButton();
    }
})();
