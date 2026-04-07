$(function() {
    const header = $('.header');
    const hederHeight = header.height();

    $(window).scroll(function() {
        if ($(this).scrollTop() > 1) {
            header.addClass('header_fixed');
            $('body').css({
                paddingTop: hederHeight + 'px'
            });
        } else {
            header.removeClass('header_fixed');
            $('body').css({
                paddingTop: 0
            });
        }

        header.css({
            padding: '0px 0',
            background: '#54744E',
            transition: '.3s'
        });
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const loadMaterialBtn = document.getElementById('loadMaterialBtn');
    const topicSelect = document.getElementById('topicSelect');
    const languageSelect = document.getElementById('languageSelect');
    const contentTypeSelect = document.getElementById('contentTypeSelect');
    const resultText = document.getElementById('resultText');
    const resultImage = document.getElementById('resultImage');
    const loadingText = document.getElementById('loadingText');
    const historyList = document.getElementById('historyList');

    if (
        !loadMaterialBtn ||
        !topicSelect ||
        !languageSelect ||
        !contentTypeSelect ||
        !resultText ||
        !resultImage ||
        !loadingText ||
        !historyList
    ) {
        return;
    }

    const TOPIC_LABELS = {
        water_pollution: { ru: 'Загрязнение воды', en: 'Water pollution' },
        recycling: { ru: 'Переработка', en: 'Recycling' },
        clean_air: { ru: 'Чистый воздух', en: 'Clean air' },
        eco_habits: { ru: 'Эко-привычки', en: 'Eco habits' },
        protecting_animals: { ru: 'Защита животных', en: 'Protecting animals' }
    };

    function escapeHtml(value) {
        return String(value)
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#039;');
    }

    function formatDate(isoString) {
        const date = new Date(isoString);
        if (Number.isNaN(date.getTime())) {
            return isoString;
        }
        return date.toLocaleString();
    }

    function getTopicLabel(topic, language) {
        if (TOPIC_LABELS[topic] && TOPIC_LABELS[topic][language]) {
            return TOPIC_LABELS[topic][language];
        }
        return topic;
    }

    function renderResult(material) {
        resultText.textContent = '';
        resultImage.style.display = 'none';
        resultImage.removeAttribute('src');

        if (material.content_type === 'text') {
            resultText.textContent = material.result_value;
            return;
        }

        if (material.content_type === 'checklist') {
            resultImage.src = material.result_value;
            resultImage.style.display = 'block';
        }
    }

    function renderHistory(items) {
        if (!items.length) {
            historyList.innerHTML = '<p class="history_empty">No requests yet.</p>';
            return;
        }

        historyList.innerHTML = items.map((item) => {
            const topicLabel = getTopicLabel(item.topic, item.language);
            const typeLabel = item.content_type === 'text' ? 'text' : 'checklist';
            const valuePreview = item.content_type === 'text'
                ? escapeHtml(String(item.result_value).slice(0, 120)) + '...'
                : escapeHtml(item.result_value);

            return `
                <div class="history_item">
                    <p class="history_meta"><strong>${escapeHtml(topicLabel)}</strong> • ${escapeHtml(item.language)} • ${escapeHtml(typeLabel)} • ${escapeHtml(formatDate(item.created_at))}</p>
                    <p class="history_result">${valuePreview}</p>
                </div>
            `;
        }).join('');
    }

    async function loadHistory() {
        try {
            const response = await fetch('/api/history');
            if (!response.ok) {
                throw new Error('History request failed');
            }
            const data = await response.json();
            renderHistory(data.items || []);
        } catch (error) {
            historyList.innerHTML = '<p class="history_empty">History unavailable right now.</p>';
            console.error(error);
        }
    }

    loadMaterialBtn.addEventListener('click', async function() {
        const topic = topicSelect.value;
        const language = languageSelect.value;
        const content_type = contentTypeSelect.value;

        loadingText.textContent = 'Loading material...';
        resultText.textContent = '';
        resultImage.style.display = 'none';

        try {
            const response = await fetch('/api/material', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ topic, language, content_type })
            });

            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(data.detail || 'Failed to load material');
            }

            renderResult(data);
            loadingText.textContent = '';
            await loadHistory();
        } catch (error) {
            loadingText.textContent = '';
            resultText.textContent = `Error: ${error.message}`;
            console.error(error);
        }
    });

    loadHistory();
});
