# Sistema de Captação de Leads - Anderson Enside Madeiras

## 📋 Visão Geral

Sistema completo de captação de leads para cotação de frete de madeira, desenvolvido com HTML5, CSS3, JavaScript e integração com Google Sheets via Apps Script.

## 🎯 Características Principais

- **3 páginas responsivas** otimizadas para conversão
- **Integração completa** com Google Sheets
- **Validações em tempo real** de formulários
- **Cálculo automático** de distâncias e valores
- **Design mobile-first** com cores de alto impacto
- **Sistema de propostas** com análise instantânea
- **Notificações automáticas** por email (opcional)

## 🚀 Instalação Rápida

### Passo 1: Configurar Google Sheets

1. **Crie uma nova planilha** no Google Sheets
   - Acesse: https://sheets.google.com
   - Clique em "+ Novo" para criar uma planilha em branco
   - Nomeie como: "Sistema Captação Fretes - Anderson Enside"

2. **Copie o ID da planilha**
   - Na URL da planilha: `https://docs.google.com/spreadsheets/d/ESTE_É_O_ID/edit`
   - Copie o ID (texto entre `/d/` e `/edit`)

### Passo 2: Configurar Google Apps Script

1. **Abra o Apps Script**
   - Na planilha, vá em: Extensões > Apps Script

2. **Configure o código**
   - Delete o código padrão `function myFunction() {}`
   - Cole todo o conteúdo do arquivo `script.gs`
   - Na linha 18, substitua `'SEU_ID_DA_PLANILHA_AQUI'` pelo ID copiado

3. **Execute a função de setup**
   - No Apps Script, selecione a função `criarEstruturaPlanilha`
   - Clique em ▶️ Executar
   - Autorize o script quando solicitado
   - Isso criará todas as abas necessárias

### Passo 3: Implantar o Web App

1. **Criar nova implantação**
   - Clique em: Implantar > Nova implantação
   - Configure:
     - Tipo: **Aplicativo Web**
     - Descrição: **API Captação de Leads**
     - Executar como: **Eu**
     - Quem pode acessar: **Qualquer pessoa**

2. **Copie a URL do Web App**
   - Após implantar, copie a URL fornecida
   - Formato: `https://script.google.com/macros/s/AKfyc.../exec`

### Passo 4: Atualizar os arquivos HTML

1. **Edite cada arquivo HTML** (index.html, cotacao.html, confirmacao.html)

2. **Adicione a URL do Web App** no JavaScript de cada página:
   ```javascript
   // Adicione esta variável no início da tag <script>
   const GOOGLE_SCRIPT_URL = 'SUA_URL_DO_WEB_APP_AQUI';
   ```

3. **Adicione a função de envio** para o Google Sheets:
   ```javascript
   async function enviarParaGoogleSheets(data) {
     try {
       const response = await fetch(GOOGLE_SCRIPT_URL, {
         method: 'POST',
         mode: 'no-cors',
         headers: {
           'Content-Type': 'application/json',
         },
         body: JSON.stringify(data)
       });
       console.log('Dados enviados com sucesso');
       return true;
     } catch (error) {
       console.error('Erro ao enviar:', error);
       return false;
     }
   }
   ```

4. **Integre nos formulários** existentes:
   ```javascript
   // No submit do formulário, adicione:
   await enviarParaGoogleSheets({
     type: 'lead', // ou 'proposta', 'rotas', 'analise'
     ...formData
   });
   ```

### Passo 5: Personalizar WhatsApp

1. **Configure seu número** do WhatsApp empresarial
2. **Edite o arquivo confirmacao.html**, linha ~398:
   ```javascript
   whatsappLink.href = `https://wa.me/55SEU_NUMERO?text=${message}`;
   ```
   Substitua `55SEU_NUMERO` pelo seu número (ex: `5517991234567`)

## 📁 Estrutura de Arquivos

```
sistema-captacao-fretes/
│
├── index.html          # Página de captura inicial
├── cotacao.html        # Página de propostas e qualificação
├── confirmacao.html    # Página de confirmação e análise
├── script.gs           # Google Apps Script
├── README.md           # Este arquivo
└── dados-rotas.json    # Dados de exemplo
```

## 📊 Estrutura das Planilhas

O sistema criará automaticamente 5 abas:

### 1. **Leads Captura**
- Timestamp
- WhatsApp
- Nome
- Tipo Veículo
- Rotas consultadas
- Device/IP

### 2. **Propostas Detalhadas**
- Todas as propostas de frete
- Cálculos automáticos de diferença
- Valor por KM e tonelada

### 3. **Rotas Favoritas**
- Rotas preferenciais dos motoristas
- Preços praticados
- Perfil do transportador

### 4. **Análise Final**
- Resumo consolidado
- Status de aprovação
- Próximos passos

### 5. **Fretes Urgentes**
- Propostas para cargas urgentes
- Priorização automática

## 🎨 Personalização

### Cores da Marca
```css
--vermelho: #DC2626;    /* CTAs principais */
--preto: #1F2937;       /* Textos */
--dourado: #F59E0B;     /* Destaques */
--branco: #FFFFFF;      /* Fundos */
```

### Adicionar Novas Rotas
Edite o objeto `distancias` no JavaScript:
```javascript
const distancias = {
  "ESTADO-Cidade_ESTADO-Cidade": 1234,
  // Adicione suas rotas aqui
}
```

### Configurar Email de Notificação
No arquivo `script.gs`, linha ~371:
```javascript
const emailDestino = 'seu-email@gmail.com';
// Descomente a linha de envio:
// MailApp.sendEmail(emailDestino, assunto, '', { htmlBody: corpo });
```

## 🔧 Solução de Problemas

### Erro: "Não autorizado"
- Execute novamente a função `criarEstruturaPlanilha`
- Autorize todas as permissões solicitadas

### Dados não chegam na planilha
1. Verifique se a URL do Web App está correta
2. Teste a URL diretamente no navegador (deve mostrar mensagem de sucesso)
3. Verifique o console do navegador para erros

### Erro de CORS
- É normal ver avisos de CORS no console
- Use `mode: 'no-cors'` no fetch (já configurado)
- Os dados serão enviados mesmo com o aviso

## 📱 Deploy em Produção

### Opção 1: GitHub Pages (Gratuito)
1. Crie um repositório no GitHub
2. Faça upload dos arquivos HTML
3. Ative GitHub Pages nas configurações
4. Acesse via: `https://seu-usuario.github.io/nome-repositorio`

### Opção 2: Netlify (Gratuito)
1. Acesse https://netlify.com
2. Arraste a pasta com os arquivos
3. Deploy automático em segundos
4. URL personalizada disponível

### Opção 3: Servidor Próprio
1. Faça upload via FTP
2. Configure HTTPS (recomendado)
3. Adicione analytics (opcional)

## 📈 Métricas e Analytics

### Google Analytics
Adicione antes do `</head>`:
```html
<!-- Global site tag (gtag.js) - Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

### Facebook Pixel
```html
<!-- Facebook Pixel Code -->
<script>
  !function(f,b,e,v,n,t,s)
  {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
  n.callMethod.apply(n,arguments):n.queue.push(arguments)};
  if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
  n.queue=[];t=b.createElement(e);t.async=!0;
  t.src=v;s=b.getElementsByTagName(e)[0];
  s.parentNode.insertBefore(t,s)}(window, document,'script',
  'https://connect.facebook.net/en_US/fbevents.js');
  fbq('init', 'YOUR_PIXEL_ID');
  fbq('track', 'PageView');
</script>
```

## 🔒 Segurança

1. **Nunca compartilhe** o ID da sua planilha publicamente
2. **Use HTTPS** sempre que possível
3. **Valide dados** tanto no frontend quanto no Apps Script
4. **Configure permissões** adequadas no Google Sheets
5. **Faça backups** regulares da planilha

## 🚦 Checklist de Lançamento

- [ ] Google Sheets configurado
- [ ] Apps Script implantado
- [ ] URLs atualizadas nos HTMLs
- [ ] WhatsApp configurado
- [ ] Testes em mobile realizados
- [ ] Analytics instalado
- [ ] Backup da planilha feito
- [ ] Email de notificação testado
- [ ] Domínio/hospedagem configurado
- [ ] SSL/HTTPS ativado

## 📞 Suporte

**Anderson Enside**
- WhatsApp: (17) 99123-4567
- Email: anderson@ensideanderson.com
- Site: https://ensideanderson.com

## 📄 Licença

Este sistema foi desenvolvido exclusivamente para Anderson Enside Madeiras.
Todos os direitos reservados © 2024

---

**Desenvolvido com ❤️ para revolucionar o mercado de fretes de madeira no Brasil**
