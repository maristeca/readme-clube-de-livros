from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
import os
from werkzeug.utils import secure_filename

# --- Configurações ---
UPLOAD_LIVROS_FOLDER = 'static/img/livros'
UPLOAD_AVATAR_FOLDER = 'static/img/avatares'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
DATABASE = 'leituraplay.db'

app = Flask(__name__)
app.secret_key = "dev-secret-mari"
app.config['UPLOAD_LIVROS_FOLDER'] = UPLOAD_LIVROS_FOLDER
app.config['UPLOAD_AVATAR_FOLDER'] = UPLOAD_AVATAR_FOLDER


# --- Funções auxiliares ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def esta_logado():
    return session.get('logado', False)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def normalize_path_for_web(path):
    """Garante que o caminho do DB esteja sempre no formato 'web' (com barras /) 
       e sem o prefixo 'static/'."""
    if not path:
        return 'img/avatar.png' # Retorna avatar padrão se o caminho for nulo
    
    # Substitui barras invertidas por barras normais
    normalized = path.replace('\\', '/')
    # Remove o prefixo 'static/' se existir
    if normalized.startswith('static/'):
        normalized = normalized[7:]
        
    return normalized


GENEROSS = ["Romance", "Ficção", "Biografia", "Infantil", "Aventura", "Juvenil", "Clássico"]


# --- Rotas principais ---
@app.route('/')
def index():
    return render_template('index.html', logado=esta_logado())


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        with get_db_connection() as conn:
            c = conn.cursor()
            # Adiciona 'lidos' na busca
            c.execute('SELECT id, nome, senha, avatar, indicacoes, lidos FROM usuarios WHERE email = ?', (email,))
            user = c.fetchone()

        if user and user['senha'] == senha:  # (em produção, usar hash)
            session['logado'] = True
            session['usuario_id'] = user['id']
            session['nome'] = user['nome']
            # CORREÇÃO/NORMALIZAÇÃO: Garante que o avatar na sessão usa o caminho web
            session['avatar'] = normalize_path_for_web(user['avatar'])
            session['lidos'] = user['lidos'] # Salva a contagem de lidos na sessão
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('feed'))
        else:
            flash('Email ou senha incorretos.', 'danger')

    return render_template('login.html', logado=esta_logado())


@app.route('/cadastro')
def cadastro():
    if esta_logado():
        return redirect(url_for('feed'))
    return render_template('cadastro.html', logado=esta_logado())


@app.route('/processar_cadastro', methods=['POST'])
def processar_cadastro():
    nome = request.form['nome']
    email = request.form['email']
    senha = request.form['senha']

    if not nome or not email or not senha:
        flash('Preencha todos os campos.', 'danger')
        return redirect(url_for('cadastro'))

    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            # Inclui o campo 'lidos' com valor inicial 0
            c.execute('INSERT INTO usuarios (nome, email, senha, lidos) VALUES (?, ?, ?, 0)', (nome, email, senha))
            conn.commit()

        flash('Cadastro realizado com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))

    except sqlite3.IntegrityError:
        flash('Este email já está cadastrado.', 'danger')
        return redirect(url_for('cadastro'))


@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('index'))


@app.route('/indicar', methods=['GET', 'POST'])
def indicar():
    if not esta_logado():
        return redirect(url_for('login'))

    if request.method == 'POST':
        usuario_id = session.get('usuario_id')
        titulo = request.form['titulo']
        autor = request.form['autor']
        descricao = request.form['descricao']
        genero1 = request.form.get('genero1')
        genero2 = request.form.get('genero2')
        genero3 = request.form.get('genero3')

        # Upload de imagem da capa
        file = request.files.get('imagem')
        # Caminho da imagem padrão é 'static/img/livros/default_cover.png'
        caminho_imagem = 'static/img/livros/default_cover.png'

        if file and allowed_file(file.filename):
            filename = secure_filename(f"{usuario_id}_{titulo}_{autor}_{os.urandom(4).hex()}.{file.filename.rsplit('.', 1)[1].lower()}")
            caminho_imagem = os.path.join(app.config['UPLOAD_LIVROS_FOLDER'], filename)

            try:
                # Salva o arquivo no sistema
                file.save(caminho_imagem)
            except Exception as e:
                print(f"Erro ao salvar imagem: {e}")
                caminho_imagem = 'static/img/livros/default_cover.png'

        # O caminho que salva no DB é sempre relativo à pasta static e normalizado para web
        caminho_db = normalize_path_for_web(caminho_imagem)

        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO livros (usuario_id, titulo, autor, descricao, imagem, genero1, genero2, genero3)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (usuario_id, titulo, autor, descricao, caminho_db, genero1, genero2, genero3))

                c.execute('UPDATE usuarios SET indicacoes = indicacoes + 1 WHERE id = ?', (usuario_id,))
                conn.commit()

            flash('Livro indicado com sucesso!', 'success')
            return redirect(url_for('feed'))

        except Exception as e:
            flash(f'Erro ao salvar a indicação: {e}', 'danger')

    return render_template('indicar.html', generos=GENEROSS, logado=True)


@app.route('/feed')
def feed():
    if not esta_logado():
        return redirect(url_for('login'))

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT 
                l.titulo, l.autor, l.descricao, l.imagem, l.genero1, l.genero2, l.genero3,
                u.nome AS nome_usuario
            FROM livros l
            JOIN usuarios u ON l.usuario_id = u.id
            ORDER BY l.id DESC
        ''')
        livros_db = c.fetchall()

    books = []
    for l in livros_db:
        # CORREÇÃO/NORMALIZAÇÃO: Garante que o caminho da imagem do livro está no formato web
        image_path = normalize_path_for_web(l['imagem'])
        
        books.append({
            "title": l['titulo'],
            "author": l['autor'],
            "description": l['descricao'],
            "img": url_for('static', filename=image_path),
            "tags": [g for g in [l['genero1'], l['genero2'], l['genero3']] if g],
            "usuario_nome": l['nome_usuario']
        })

    return render_template('feed.html', books=books, logado=True)


@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if not esta_logado():
        return redirect(url_for('login'))

    usuario_id = session.get('usuario_id')

    # Se a requisição for para atualizar o avatar
    if request.method == 'POST' and 'avatar_file' in request.files:
        avatar_file = request.files.get('avatar_file')
        if avatar_file and allowed_file(avatar_file.filename):
            ext = avatar_file.filename.rsplit('.', 1)[1].lower()
            filename = secure_filename(f"avatar_{usuario_id}.{ext}")
            caminho_avatar = os.path.join(app.config['UPLOAD_AVATAR_FOLDER'], filename)

            try:
                avatar_file.save(caminho_avatar)
                with get_db_connection() as conn:
                    c = conn.cursor()
                    # Salva o caminho relativo e normalizado no DB
                    caminho_db = normalize_path_for_web(caminho_avatar)
                    c.execute('UPDATE usuarios SET avatar = ? WHERE id = ?', (caminho_db, usuario_id))
                    conn.commit()

                session['avatar'] = caminho_db
                flash("Avatar atualizado com sucesso!", "success")
            except Exception as e:
                print(f"Erro ao salvar avatar: {e}")
                flash("Erro ao salvar o avatar.", "danger")

            return redirect(url_for('perfil'))

        flash("Formato de arquivo inválido. Use PNG, JPG ou GIF.", "danger")
        return redirect(url_for('perfil'))

    # Se a requisição for GET ou se o POST for concluído:

    with get_db_connection() as conn:
        c = conn.cursor()
        # Busca lidos, nome, avatar, indicacoes
        c.execute('SELECT nome, avatar, indicacoes, lidos FROM usuarios WHERE id = ?', (usuario_id,))
        user_db = c.fetchone()

        c.execute('SELECT titulo, autor, descricao, imagem, genero1, genero2, genero3 FROM livros WHERE usuario_id = ? ORDER BY id DESC', (usuario_id,))
        livros = c.fetchall()

    user_books = []
    for l in livros:
        # CORREÇÃO/NORMALIZAÇÃO: Garante que o caminho da imagem do livro está no formato web
        image_path = normalize_path_for_web(l['imagem'])

        user_books.append({
            "title": l['titulo'],
            "author": l['autor'],
            "description": l['descricao'],
            # Converte o caminho normalizado em URL
            "img": url_for('static', filename=image_path), 
            "tags": [g for g in [l['genero1'], l['genero2'], l['genero3']] if g]
        })
    
    # CORREÇÃO/NORMALIZAÇÃO: Garante que o caminho do avatar está no formato web
    user_avatar = normalize_path_for_web(user_db['avatar']) if user_db['avatar'] else 'img/avatar.png'

    user = {
        "name": user_db['nome'],
        "bio": "A leitura é o segundo sol",
        # Converte o caminho normalizado em URL
        "avatar": url_for('static', filename=user_avatar),
        # Novo: Busca o valor real de 'lidos' do DB
        "lidos": user_db['lidos'] if user_db['lidos'] else 0,
        "indicacoes": user_db['indicacoes'],
        "books": user_books
    }

    # Remove 'medalhas' de user, pois foi substituído por 'Experiência' no HTML
    return render_template('perfil.html', user=user, logado=True)


@app.route('/atualizar_lidos', methods=['POST'])
def atualizar_lidos():
    """
    Rota chamada via AJAX/Fetch pelo botão 'Li um Livro' para incrementar a contagem.
    """
    if not esta_logado():
        return jsonify({"success": False, "message": "Não autenticado"}), 401

    usuario_id = session.get('usuario_id')
    
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            # 1. Incrementa a contagem de lidos
            c.execute('UPDATE usuarios SET lidos = lidos + 1 WHERE id = ?', (usuario_id,))
            conn.commit()
            
            # 2. Busca a nova contagem para retornar ao front-end
            c.execute('SELECT lidos FROM usuarios WHERE id = ?', (usuario_id,))
            nova_contagem = c.fetchone()['lidos']
            
            # Atualiza a sessão
            session['lidos'] = nova_contagem
            
            return jsonify({"success": True, "lidos": nova_contagem})
            
    except Exception as e:
        print(f"Erro ao atualizar livros lidos: {e}")
        return jsonify({"success": False, "message": "Erro no servidor"}), 500


@app.route('/estatisticas')
def estatisticas():
    if not esta_logado():
        return redirect(url_for('login'))

    usuario_id = session.get('usuario_id')
    with get_db_connection() as conn:
        c = conn.cursor()
        
        # Busca Lidos e Indicações
        c.execute('SELECT indicacoes, lidos FROM usuarios WHERE id = ?', (usuario_id,))
        stats_db = c.fetchone()

    stats = {
        "lidos": stats_db['lidos'] if stats_db and stats_db['lidos'] else 0,
        "indicacoes": stats_db['indicacoes'] if stats_db and stats_db['indicacoes'] else 0,
    }

    # O campo "medalhas" foi removido/substituído.
    return render_template('estatisticas.html', stats=stats, logado=True)


# --- Inicialização ---
def init_db():
    # Cria as pastas de upload se não existirem
    if not os.path.exists(UPLOAD_LIVROS_FOLDER):
        os.makedirs(UPLOAD_LIVROS_FOLDER)
    if not os.path.exists(UPLOAD_AVATAR_FOLDER):
        os.makedirs(UPLOAD_AVATAR_FOLDER)

    # Garante que a imagem padrão exista (ou pelo menos a pasta)
    avatar_padrao_dir = os.path.join('static', 'img')
    if not os.path.exists(avatar_padrao_dir):
        os.makedirs(avatar_padrao_dir)

    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        # Tenta adicionar a coluna 'lidos' se ela ainda não existir
        try:
            c.execute('ALTER TABLE usuarios ADD COLUMN lidos INTEGER DEFAULT 0')
            print("Coluna 'lidos' adicionada à tabela usuarios.")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' not in str(e):
                 # Ignora se a coluna já existe
                print(f"Erro ao adicionar coluna 'lidos' (Pode ser que já exista): {e}")

        c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            -- Caminho relativo 'img/avatar.png'
            avatar TEXT DEFAULT 'img/avatar.png', 
            indicacoes INTEGER DEFAULT 0
            -- A coluna 'lidos' já foi verificada e adicionada via ALTER TABLE
        )
        ''')

        c.execute('''
        CREATE TABLE IF NOT EXISTS livros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            autor TEXT NOT NULL,
            descricao TEXT,
            imagem TEXT,
            genero1 TEXT,
            genero2 TEXT,
            genero3 TEXT,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
        ''')

        # Cria usuário de teste
        c.execute('SELECT * FROM usuarios WHERE email = ?', ('ana@play.com',))
        if c.fetchone() is None:
            c.execute('INSERT INTO usuarios (nome, email, senha, avatar, indicacoes, lidos) VALUES (?, ?, ?, ?, ?, ?)',
                      ('Ana Leitora', 'ana@play.com', '123456', 'img/avatar.png', 5, 12)) # 12 lidos para teste

        conn.commit()
        conn.close()
        print("Banco de dados e tabelas verificados/criados com sucesso!")

    except Exception as e:
        print(f"Erro ao inicializar o banco de dados: {e}")


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
