import os
import subprocess
import re
import json
import math
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(math.isqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/encrypt-decrypt', methods=['POST'])
def encrypt_decrypt():
    data = request.get_json() or {}
    message = data.get('message', '')
    
    try:
        p = int(data.get('p', 997))
        q = int(data.get('q', 883))
        e = int(data.get('e', 13))
    except (ValueError, TypeError):
        return jsonify({'error': 'p, q, e 값은 올바른 정수여야 합니다.'}), 400

    if not message:
        return jsonify({'error': '메시지를 입력해주세요.'}), 400

    # If parameters match the fixed rsa.py values, run rsa.py as subprocess
    if p == 997 and q == 883 and e == 13:
        try:
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            process = subprocess.run(
                ['python', 'rsa.py'],
                input=message,
                capture_output=True,
                text=True,
                encoding='utf-8',
                env=env,
                timeout=5
            )
            
            stdout = process.stdout
            stderr = process.stderr
            
            if process.returncode != 0:
                return jsonify({
                    'error': 'rsa.py 실행 중 에러가 발생했습니다.',
                    'details': stderr
                }), 500

            d_match = re.search(r'구해진 개인키 d:\s*(\d+)', stdout)
            m_match = re.search(r'암호화 결과 m:\s*(\[.*?\])', stdout)
            result_match = re.search(r'복호화 결과:\s*(.*)', stdout, re.DOTALL)
            
            if not d_match or not m_match or not result_match:
                return jsonify({
                    'error': 'rsa.py의 출력 결과를 파싱하는 데 실패했습니다.',
                    'raw_stdout': stdout
                }), 500

            d_val = int(d_match.group(1))
            try:
                m_list = json.loads(m_match.group(1))
            except Exception:
                m_list = m_match.group(1)
                
            decrypted_msg = result_match.group(1).strip()

            return jsonify({
                'success': True,
                'method': 'rsa.py 실행 (Subprocess)',
                'p': p,
                'q': q,
                'e': e,
                'n': p * q,
                'phi': (p - 1) * (q - 1),
                'd': d_val,
                'ciphertext': m_list,
                'decrypted': decrypted_msg
            })
            
        except subprocess.TimeoutExpired:
            return jsonify({'error': '시간 초과가 발생했습니다.'}), 504
        except Exception as err:
            return jsonify({'error': f'서버 오류: {str(err)}'}), 500

    # For other parameter sets, calculate server-side using the same RSA logic
    else:
        if not is_prime(p) or not is_prime(q):
            return jsonify({'error': 'p와 q는 모두 소수(Prime Number)여야 합니다.'}), 400
        
        n = p * q
        phi = (p - 1) * (q - 1)
        
        if math.gcd(e, phi) != 1:
            return jsonify({'error': f'e({e})와 φ(n)({phi})은 서로소(Coprime)여야 합니다. 서로소인 값을 입력해주세요.'}), 400
        
        try:
            d = pow(e, -1, phi)
        except ValueError:
            d = 1
            found = False
            for _ in range(1000000):
                if (e * d) % phi == 1:
                    found = True
                    break
                d += 1
            if not found:
                return jsonify({'error': '개인키 d를 찾을 수 없습니다.'}), 400

        # 문자의 유니코드 값이 n보다 크면 암호화/복호화가 불가능
        too_large = []
        for char in message:
            code = ord(char)
            if code >= n:
                too_large.append({'char': char, 'unicode': code})
        
        if too_large:
            samples = too_large[:5]  # 최대 5개만 표시
            char_list = ', '.join([f"'{item['char']}' (U+{item['unicode']:04X}, 값: {item['unicode']})" for item in samples])
            return jsonify({
                'error': f'암호화 실패: 메시지에 포함된 문자의 유니코드 값이 n({n})보다 크거나 같아 암호화할 수 없습니다.',
                'details': f'문제 문자: {char_list}' + (f' 외 {len(too_large) - 5}개' if len(too_large) > 5 else ''),
                'hint': f'RSA에서는 평문 값이 반드시 n보다 작아야 합니다. 한국어(유니코드 범위: 44032~55203)를 암호화하려면 n이 최소 55204 이상이어야 합니다. 현재 n = p×q = {p}×{q} = {n}입니다. 더 큰 소수 p, q를 선택해주세요.'
            }), 400

        m_list = []
        decrypted_chars = []
        
        for char in message:
            cipher_char = pow(ord(char), e, n)
            m_list.append(cipher_char)
            plain_char_code = pow(cipher_char, d, n)
            decrypted_chars.append(chr(plain_char_code))
            
        decrypted_msg = "".join(decrypted_chars)

        return jsonify({
            'success': True,
            'method': '서버 자체 계산 (동적 매개변수)',
            'p': p,
            'q': q,
            'e': e,
            'n': n,
            'phi': phi,
            'd': d,
            'ciphertext': m_list,
            'decrypted': decrypted_msg
        })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
