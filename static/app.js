function onPresetChange() {
    const select = document.getElementById('preset-select');
    const customRow = document.getElementById('custom-inputs');
    const val = select.value;

    const pInput = document.getElementById('input-p');
    const qInput = document.getElementById('input-q');
    const eInput = document.getElementById('input-e');

    if (val === 'custom') {
        customRow.classList.remove('hidden');
    } else {
        customRow.classList.add('hidden');
        if (val === 'default') {
            pInput.value = 997;
            qInput.value = 883;
            eInput.value = 13;
        } else if (val === 'preset-small') {
            pInput.value = 61;
            qInput.value = 53;
            eInput.value = 17;
        } else if (val === 'preset-basic') {
            pInput.value = 17;
            qInput.value = 19;
            eInput.value = 5;
        }
    }
}

async function handleEncrypt(event) {
    event.preventDefault();
    
    const textarea = document.getElementById('message-input');
    const submitBtn = document.getElementById('submit-btn');
    const emptyState = document.getElementById('empty-state');
    const resultsContent = document.getElementById('results-content');
    const errorBanner = document.getElementById('error-banner');
    
    const message = textarea.value.trim();
    if (!message) return;

    // Get current values
    const p = parseInt(document.getElementById('input-p').value);
    const q = parseInt(document.getElementById('input-q').value);
    const e = parseInt(document.getElementById('input-e').value);

    if (isNaN(p) || isNaN(q) || isNaN(e)) {
        alert('p, q, e 값은 올바른 숫자여야 합니다.');
        return;
    }

    // Hide previous states
    errorBanner.classList.add('hidden');
    resultsContent.classList.add('hidden');

    // Set loading state
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;
    submitBtn.querySelector('span').innerText = '처리 중...';

    try {
        const response = await fetch('/api/encrypt-decrypt', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                message: message,
                p: p,
                q: q,
                e: e
            })
        });

        const data = await response.json();
        
        if (!response.ok) {
            // Show inline error banner
            emptyState.classList.add('hidden');
            resultsContent.classList.add('hidden');
            errorBanner.classList.remove('hidden');

            document.getElementById('error-title').innerText = data.error || '알 수 없는 에러가 발생했습니다.';
            document.getElementById('error-details').innerText = data.details || '';
            document.getElementById('error-hint').innerText = data.hint || '';

            // Hide details/hint lines if empty
            document.getElementById('error-details').style.display = data.details ? 'block' : 'none';
            document.getElementById('error-hint').style.display = data.hint ? 'block' : 'none';
            return;
        }

        // Update parameters
        document.getElementById('val-p').innerText = data.p;
        document.getElementById('val-q').innerText = data.q;
        document.getElementById('val-e').innerText = data.e;
        document.getElementById('val-n').innerText = data.n.toLocaleString();
        document.getElementById('val-phi').innerText = data.phi.toLocaleString();
        document.getElementById('val-d').innerText = data.d;

        // Show execution method
        document.getElementById('execution-method').innerText = `연산 방식: ${data.method || '일반'}`;

        // Update outputs
        document.getElementById('res-original').innerText = message;
        document.getElementById('res-ciphertext').innerText = JSON.stringify(data.ciphertext);
        document.getElementById('res-decrypted').innerText = data.decrypted;

        // Toggle views
        emptyState.classList.add('hidden');
        errorBanner.classList.add('hidden');
        resultsContent.classList.remove('hidden');

    } catch (error) {
        alert('네트워크 에러: ' + error.message);
    } finally {
        // Restore button state
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
        submitBtn.querySelector('span').innerText = '암호화 & 복호화 실행';
    }
}
