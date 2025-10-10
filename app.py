from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from werkzeug.utils import secure_filename

# --- Configurações ---
# Diretórios de upload
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
            c.execute('SELECT id, nome, senha, avatar, indicacoes FROM usuarios WHERE email = ?', (email,))
            user = c.fetchone()

        if user and user['senha'] == senha: # Em um app real, use hash de senha!
            session['logado'] = True
            session['usuario_id'] = user['id']
            session['nome'] = user['nome']
            session['avatar'] = user['avatar']
            flash('Login bem-sucedido!', 'success')
            return redirect(url_for('perfil'))
        else:
            flash('Email ou senha incorretos.', 'danger')
            return render_template('login.html')
            
    return render_template('login.html', logado=esta_logado())

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        
        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                c.execute('INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)', (nome, email, senha))
                conn.commit()
            flash('Cadastro realizado com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Este email já está cadastrado.', 'danger')
            return render_template('cadastro.html')

    return render_template('cadastro.html', logado=esta_logado())

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
        
        # Lógica de upload da imagem da capa
        file = request.files.get('imagem')
        caminho_imagem = 'static/img/livros/default_cover.png' # Fallback
        
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{usuario_id}_{titulo}_{autor}_{os.urandom(4).hex()}.{file.filename.rsplit('.', 1)[1].lower()}")
            caminho_imagem = os.path.join(app.config['UPLOAD_LIVROS_FOLDER'], filename)
            
            try:
                file.save(caminho_imagem)
            except Exception as e:
                print(f"Erro ao salvar arquivo: {e}")
                caminho_imagem = 'static/img/livros/default_cover.png'


        try:
            with get_db_connection() as conn:
                c = conn.cursor()
                # 1. Salva a indicação do livro
                c.execute('''
                    INSERT INTO livros (usuario_id, titulo, autor, descricao, imagem, genero1, genero2, genero3)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (usuario_id, titulo, autor, descricao, caminho_imagem, genero1, genero2, genero3))
                
                # 2. Incrementa o contador de indicações do usuário
                c.execute('UPDATE usuarios SET indicacoes = indicacoes + 1 WHERE id = ?', (usuario_id,))
                conn.commit()
            
            # Atualiza a sessão para refletir o novo número (opcional, mas bom)
            session['indicacoes'] = session.get('indicacoes', 0) + 1
            
            flash('Livro indicado com sucesso! Aparecerá no Feed.', 'success')
            return redirect(url_for('feed'))

        except Exception as e:
            flash(f'Erro ao salvar a indicação: {e}', 'danger')
            return redirect(url_for('indicar'))

    return render_template('indicar.html', generos=GENEROSS, logado=True)

@app.route('/feed')
def feed():
    if not esta_logado():
        return redirect(url_for('login'))
    
    with get_db_connection() as conn:
        c = conn.cursor()
        # Busca livros com o nome do usuário que indicou
        c.execute('''
            SELECT 
                l.titulo, l.autor, l.descricao, l.imagem, l.genero1, l.genero2, l.genero3,
                u.nome as nome_usuario
            FROM livros l
            JOIN usuarios u ON l.usuario_id = u.id
            ORDER BY l.id DESC
        ''')
        livros_db = c.fetchall()

    books = []
    for l in livros_db:
        books.append({
            "title": l['titulo'],
            "author": l['autor'],
            "description": l['descricao'], 
            # Garante que o caminho da imagem esteja correto para o Flask
            "img": url_for('static', filename=l['imagem'].replace('static/', '').replace('\\','/')), 
            "tags": [g for g in [l['genero1'], l['genero2'], l['genero3']] if g],
            "usuario_nome": l['nome_usuario']
        })

    return render_template('feed.html', books=books, logado=True)

@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if not esta_logado():
        return redirect(url_for('login'))

    usuario_id = session.get('usuario_id')
    
    # Lógica para processar a mudança de avatar (POST)
    if request.method == 'POST':
        avatar_file = request.files.get('avatar_file')
        
        if avatar_file and allowed_file(avatar_file.filename):
            # Cria um nome único para o avatar
            ext = avatar_file.filename.rsplit('.', 1)[1].lower()
            filename = secure_filename(f"avatar_{usuario_id}.{ext}")
            # Usando caminho relativo para salvar no DB
            caminho_avatar = os.path.join(app.config['UPLOAD_AVATAR_FOLDER'], filename)
            
            try:
                # Salva o arquivo no sistema de arquivos
                avatar_file.save(caminho_avatar)
                
                with get_db_connection() as conn:
                    c = conn.cursor()
                    # Salva o caminho relativo (ex: 'img/avatares/avatar_1.jpg')
                    c.execute('UPDATE usuarios SET avatar = ? WHERE id = ?', 
                              (caminho_avatar.replace('static/', ''), usuario_id))
                    conn.commit()
                
                # Atualiza a sessão
                session['avatar'] = caminho_avatar.replace('static/', '')

                flash("Avatar atualizado com sucesso!", "success")
            except Exception as e:
                print(f"Erro ao salvar o avatar: {e}")
                flash("Erro ao salvar o avatar.", "danger")
            
            return redirect(url_for('perfil'))
        
        flash("Formato de arquivo inválido. Use PNG, JPG ou GIF.", "danger")
        return redirect(url_for('perfil'))


    # Lógica GET para exibir o perfil (Busca de dados)
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT nome, avatar, indicacoes FROM usuarios WHERE id = ?', (usuario_id,))
        user_db = c.fetchone()
        
        c.execute('SELECT titulo, autor, descricao, imagem, genero1, genero2, genero3 FROM livros WHERE usuario_id = ? ORDER BY id DESC', (usuario_id,))
        livros = c.fetchall()

    user_books = []
    for l in livros:
        user_books.append({
            "title": l['titulo'],
            "author": l['autor'],
            "description": l['descricao'],
            "img": url_for('static', filename=l['imagem'].replace('static/', '').replace('\\','/')),
            "tags": [g for g in [l['genero1'], l['genero2'], l['genero3']] if g]
        })

    user = {
        "name": user_db['nome'],
        "bio": "A leitura é o segundo sol",
        "avatar": url_for('static', filename=user_db['avatar'].replace('\\','/')), # Já tem static/
        "lidos": 10,
        "indicacoes": user_db['indicacoes'],
        "medalhas": ["Leitor dedicado"],
        "books": user_books
    }

    return render_template('perfil.html', user=user, logado=True)

@app.route('/estatisticas')
def estatisticas():
    if not esta_logado():
        return redirect(url_for('login'))

    usuario_id = session.get('usuario_id')

    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('SELECT indicacoes FROM usuarios WHERE id = ?', (usuario_id,))
        indicacoes_db = c.fetchone()
        
        # MOCK data for other stats
        total_indicacoes_geral = c.execute('SELECT COUNT(*) FROM livros').fetchone()[0]
        
    stats = {
        "indicacoes_feitas": indicacoes_db['indicacoes'] if indicacoes_db else 0,
        "livros_lidos": 10, # Valor fixo/mock
        "total_indicacoes_geral": total_indicacoes_geral
    }

    return render_template('estatisticas.html', stats=stats, logado=True)

# --- Inicialização ---

def init_db():
    # Cria os diretórios de uploads
    if not os.path.exists(UPLOAD_LIVROS_FOLDER):
        os.makedirs(UPLOAD_LIVROS_FOLDER)
    if not os.path.exists(UPLOAD_AVATAR_FOLDER):
        os.makedirs(UPLOAD_AVATAR_FOLDER)
    
    # Cria uma imagem de avatar padrão se não existir
    avatar_padrao = os.path.join('static', 'img', 'avatar.png')
    if not os.path.exists(avatar_padrao):
        # Aqui, você precisaria criar um arquivo real ou garantir que ele exista.
        # Por enquanto, apenas garante o caminho para evitar erros de arquivo.
        if not os.path.exists(os.path.join('static', 'img')):
             os.makedirs(os.path.join('static', 'img'))


    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        # Tabela de usuários (SQL LIMPO - SEM COMENTÁRIOS DE PYTHON INTERNOS)
        c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            avatar TEXT DEFAULT 'img/avatar.png',
            indicacoes INTEGER DEFAULT 0
        )
        ''')

        # Tabela de livros indicados (SQL LIMPO - SEM COMENTÁRIOS DE PYTHON INTERNOS)
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
        
        # Insere usuário de teste se não existir
        c.execute('SELECT * FROM usuarios WHERE email = ?', ('ana@play.com',))
        if c.fetchone() is None:
            c.execute('INSERT INTO usuarios (nome, email, senha, avatar, indicacoes) VALUES (?, ?, ?, ?, ?)', 
                      ('Ana Leitora', 'ana@play.com', '123456', 'img/avatar.png', 0))

        conn.commit()
        conn.close()
        print("Banco de dados e tabelas verificados/criados com sucesso!")
    except Exception as e:
        print(f"Erro ao inicializar o banco de dados: {e}")

if __name__ == '__main__':
    init_db() # Roda a inicialização e correção do banco
    app.run(debug=True)
