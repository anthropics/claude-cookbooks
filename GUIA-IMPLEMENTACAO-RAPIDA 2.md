# 🚀 GUIA DE IMPLEMENTAÇÃO RÁPIDA - ANDERSON ENSIDE MADEIRAS

## ⏱️ Tempo Total: 30 minutos

---

## PASSO 1: CRIAR PLANILHA NO GOOGLE SHEETS (5 minutos)

### 1.1 Acesse o Google Sheets
```
https://sheets.google.com
```

### 1.2 Crie uma nova planilha
- Clique no botão **"+"** para criar planilha em branco
- Renomeie para: **"Sistema Captação Fretes - Anderson Enside"**

### 1.3 Copie o ID da sua planilha
Na URL da planilha você verá algo assim:
```
https://docs.google.com/spreadsheets/d/1ABC123def456GHI789jkl/edit
                                       ^^^^^^^^^^^^^^^^^^^^
                                       Este é o ID - COPIE!
```

**SEU ID:** _____________________________  (cole aqui para não perder)

---

## PASSO 2: CONFIGURAR O GOOGLE APPS SCRIPT (10 minutos)

### 2.1 Abra o Apps Script
Na sua planilha, clique em:
```
Extensões → Apps Script
```

### 2.2 Delete o código padrão
Apague tudo que estiver escrito (geralmente `function myFunction() {}`)

### 2.3 Cole o código do arquivo script.gs
- Abra o arquivo `script.gs` que criamos
- Copie TODO o conteúdo (Ctrl+A, Ctrl+C)
- Cole no Apps Script

### 2.4 IMPORTANTE: Substitua o ID da planilha
Na linha 18 do código, você verá:
```javascript
const SPREADSHEET_ID = 'SEU_ID_DA_PLANILHA_AQUI';
```

Substitua por:
```javascript
const SPREADSHEET_ID = 'COLE_O_ID_QUE_VOCE_COPIOU_AQUI';
```

### 2.5 Salve o projeto
- Clique no ícone de disquete 💾 ou Ctrl+S
- Nome do projeto: **"API Captação Fretes"**

### 2.6 Execute a função de configuração inicial
1. No dropdown de funções, selecione: `criarEstruturaPlanilha`
2. Clique no botão ▶️ **Executar**
3. **AUTORIZAÇÃO IMPORTANTE:**
   - Aparecerá uma janela pedindo autorização
   - Clique em **"Revisar permissões"**
   - Escolha sua conta Google
   - Clique em **"Avançado"**
   - Clique em **"Ir para API Captação Fretes (não seguro)"**
   - Clique em **"Permitir"**

✅ Quando terminar, você verá no console: "Estrutura da planilha criada com sucesso!"

### 2.7 Verifique se as abas foram criadas
Volte para sua planilha e confirme que foram criadas 5 abas:
- ✅ Leads Captura (fundo preto)
- ✅ Propostas Detalhadas (fundo vermelho)
- ✅ Rotas Favoritas (fundo verde)
- ✅ Análise Final (fundo azul)
- ✅ Fretes Urgentes (fundo dourado)

---

## PASSO 3: IMPLANTAR O WEB APP (5 minutos)

### 3.1 No Apps Script, clique em:
```
Implantar → Nova implantação
```

### 3.2 Configure a implantação:
- **Tipo:** Aplicativo Web
- **Descrição:** API Captação de Leads
- **Executar como:** Eu
- **Quem pode acessar:** Qualquer pessoa

### 3.3 Clique em "Implantar"

### 3.4 COPIE A URL DO WEB APP
Você receberá uma URL assim:
```
https://script.google.com/macros/s/AKfycbwXXXXXXXXXXXXXXXXXXXXXX/exec
```

**SUA URL:** _____________________________________________ (GUARDE ISSO!)

---

## PASSO 4: ATUALIZAR OS ARQUIVOS HTML (10 minutos)

### 4.1 Abra o arquivo `index.html` em um editor de texto

### 4.2 Localize a linha 850 (aproximadamente)
Procure por esta parte do código:
```javascript
// Event Listeners para os dropdowns
document.getElementById('estado-origem').addEventListener
```

### 4.3 Adicione ANTES dessa linha:
```javascript
// CONFIGURAÇÃO DA URL DO GOOGLE SHEETS
const GOOGLE_SCRIPT_URL = 'COLE_SUA_URL_DO_WEB_APP_AQUI';

// Função para enviar dados ao Google Sheets
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
        console.log('✅ Dados enviados para Google Sheets');
        return true;
    } catch (error) {
        console.error('❌ Erro ao enviar:', error);
        return false;
    }
}
```

### 4.4 Localize a linha com "setTimeout" (aproximadamente linha 950)
Procure por:
```javascript
setTimeout(() => {
    window.location.href = 'cotacao.html';
}, 1500);
```

### 4.5 Adicione ANTES do setTimeout:
```javascript
// Enviar para Google Sheets
await enviarParaGoogleSheets({
    type: 'lead',
    ...formData
});
```

### 4.6 Repita o processo para `cotacao.html`
- Abra o arquivo
- Adicione a mesma configuração de URL e função
- Na linha do setTimeout, adicione o envio

### 4.7 Repita para `confirmacao.html`
- Mesmo processo
- Adicione a URL e função
- Integre no código

---

## PASSO 5: CONFIGURAR SEU WHATSAPP (2 minutos)

### 5.1 Abra `confirmacao.html`

### 5.2 Localize a linha 398 (aproximadamente)
Procure por:
```javascript
whatsappLink.href = `https://wa.me/5517991234567?text=${message}`;
```

### 5.3 Substitua pelo seu número:
```javascript
whatsappLink.href = `https://wa.me/55SEUNUMERO?text=${message}`;
```

Exemplo com seu número de Araçatuba:
```javascript
whatsappLink.href = `https://wa.me/5518991234567?text=${message}`;
```

---

## PASSO 6: TESTAR O SISTEMA (3 minutos)

### 6.1 Teste Local
1. Abra `index.html` no navegador
2. Preencha o formulário com dados de teste:
   - WhatsApp: (18) 99123-4567
   - Nome: Teste Anderson
   - Veículo: Carreta LS
3. Clique em "QUERO MINHA COTAÇÃO AGORA"
4. Você deve ser direcionado para a página 2
5. Faça algumas propostas
6. Envie e chegue até a página 3

### 6.2 Verifique o Google Sheets
1. Abra sua planilha
2. Verifique se os dados apareceram nas abas
3. Se não apareceram, verifique o console do navegador (F12)

---

## PASSO 7: PUBLICAR ONLINE (5 minutos)

### OPÇÃO A: GitHub Pages (Gratuito e Rápido)

1. Crie conta no GitHub: https://github.com
2. Crie novo repositório: "sistema-captacao-fretes"
3. Faça upload dos 3 arquivos HTML
4. Vá em Settings → Pages
5. Source: Deploy from a branch
6. Branch: main, folder: / (root)
7. Save
8. Aguarde 5 minutos
9. Acesse: https://seu-usuario.github.io/sistema-captacao-fretes

### OPÇÃO B: Netlify (Ainda Mais Rápido)

1. Acesse: https://netlify.com
2. Arraste a pasta com os 3 HTMLs para a área indicada
3. Pronto! Site no ar em segundos
4. URL gerada automaticamente

### OPÇÃO C: Seu Domínio Próprio

Se você tem o domínio ensideanderson.com:
1. Faça upload via FTP dos 3 arquivos HTML
2. Crie uma pasta: /cotacao/
3. Coloque os arquivos dentro
4. Acesse: https://ensideanderson.com/cotacao/

---

## 🎯 CHECKLIST FINAL

- [ ] Planilha Google Sheets criada
- [ ] ID da planilha copiado
- [ ] Apps Script configurado
- [ ] Função criarEstruturaPlanilha executada
- [ ] 5 abas criadas na planilha
- [ ] Web App implantado
- [ ] URL do Web App copiada
- [ ] URL adicionada nos 3 HTMLs
- [ ] Número do WhatsApp configurado
- [ ] Teste local realizado
- [ ] Dados chegando na planilha
- [ ] Site publicado online
- [ ] Link compartilhado com equipe

---

## 🚨 PROBLEMAS COMUNS E SOLUÇÕES

### Problema 1: "Não autorizado" no Apps Script
**Solução:** Execute novamente a função e aceite todas as permissões

### Problema 2: Dados não chegam na planilha
**Solução:** 
1. Verifique se a URL do Web App está correta
2. Teste a URL no navegador (deve mostrar mensagem)
3. Verifique o console (F12) para erros

### Problema 3: Erro de CORS
**Solução:** É normal! Use mode: 'no-cors' (já configurado)

### Problema 4: WhatsApp não abre
**Solução:** Verifique se o número está no formato: 5518991234567

---

## 📞 SUPORTE TÉCNICO

Se precisar de ajuda em qualquer etapa:

**WhatsApp Suporte:** (11) 99999-9999
**Email:** suporte@sistemafretes.com
**Horário:** Segunda a Sexta, 9h às 18h

---

## 🎉 PARABÉNS!

Seu sistema está pronto para captar leads 24/7!

**Próximas melhorias sugeridas:**
1. Adicionar Google Analytics
2. Configurar Facebook Pixel
3. Criar campanha no Google Ads
4. Integrar com CRM
5. Adicionar chat online

---

**Desenvolvido com ❤️ para Anderson Enside Madeiras**
