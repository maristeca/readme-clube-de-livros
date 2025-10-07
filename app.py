from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = "dev-secret-mari"

# --- Função auxiliar ---
def esta_logado():
    return session.get('logado', False)

# --- Rotas públicas ---
@app.route('/')
def index():
    return render_template('index.html', logado=esta_logado())

@app.route('/login')
def login():
    if esta_logado():
        return redirect(url_for('feed'))
    return render_template('login.html', logado=esta_logado())

@app.route('/cadastro')
def cadastro():
    if esta_logado():
        return redirect(url_for('feed'))
    return render_template('cadastro.html', logado=esta_logado())

# --- Rotas privadas ---
@app.route('/feed')
def feed():
    if not esta_logado():
        return redirect(url_for('login'))

    books = [
        {"title":"Harry Potter e a Pedra Filosofal","author":"J.K. Rowling",
         "img":url_for('static', filename='img/livro2.jpg'),
         "text":"Uma excelente aventura e leitura divertida, eu amei!","tags":["Ficção Juvenil","Aventura"]},
        {"title":"Dom Casmurro","author":"Machado de Assis",
         "img":url_for('static', filename='img/livro1.webp'),
         "text":"Denso e clássico, muito interessante para debates.","tags":["Clássico","Romance"]}
    ]
    return render_template('feed.html', books=books, logado=True)

@app.route('/comunidades')
def comunidades():
    if not esta_logado():
        return redirect(url_for('login'))
    return render_template('comunidades.html', logado=True)

@app.route('/perfil')
def perfil():
    if not esta_logado():
        return redirect(url_for('login'))

    user = {
        "name": "Ana Banana Machadinho",
        "bio": "A leitura é o segundo sol",
        "avatar": url_for('static', filename='img/avatar.png'),
        "lidos": 18,
        "indicacoes": 21,
        "medalhas": 10
    }
    return render_template('perfil.html', user=user, logado=True)

@app.route('/avaliar')
def avaliar():
    if not esta_logado():
        return redirect(url_for('login'))
    return render_template('avaliar.html', logado=True)

@app.route('/estatisticas')
def estatisticas():
    if not esta_logado():
        return redirect(url_for('login'))
    return render_template('estatisticas.html', logado=True)

# --- Rotas de processamento ---
@app.route('/entrar', methods=['POST'])
def processar_login():
    email = request.form.get('email')
    senha = request.form.get('senha')
    if email and senha:
        session['logado'] = True
        flash("Login realizado com sucesso!", "success")
        return redirect(url_for('feed'))
    flash("Preencha email e senha.", "danger")
    return redirect(url_for('login'))

@app.route('/cadastrar_novo', methods=['POST'])
def processar_cadastro():
    nome = request.form.get('nome')
    email = request.form.get('email')
    senha = request.form.get('senha')
    if nome and email and senha:
        session['logado'] = True
        flash(f"Usuário {nome} cadastrado com sucesso!", "success")
        return redirect(url_for('feed'))
    flash("Preencha todos os campos.", "danger")
    return redirect(url_for('cadastro'))

@app.route('/avaliar_enviar', methods=['POST'])
def enviar_avaliacao():
    comentario = request.form.get('comentario')
    flash("Avaliação enviada (simulação). Obrigada!", "success")
    return redirect(url_for('feed'))

@app.route('/logout')
def logout():
    session.clear()
    flash("Você saiu da conta.", "success")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
