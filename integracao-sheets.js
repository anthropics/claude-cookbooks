/**
 * Sistema de Integração com Google Sheets
 * Anderson Enside Madeiras - Captação de Leads
 * 
 * Este arquivo contém todas as funções necessárias para
 * integrar os formulários HTML com o Google Sheets
 */

// ========================================
// CONFIGURAÇÃO INICIAL - MUITO IMPORTANTE
// ========================================

// SUBSTITUA esta URL pela URL do seu Web App do Google Apps Script
const GOOGLE_SCRIPT_URL = 'https://script.google.com/macros/s/YOUR_SCRIPT_ID_HERE/exec';

// Configuração de retry e timeout
const CONFIG = {
    maxRetries: 3,
    retryDelay: 1000, // 1 segundo
    timeout: 10000, // 10 segundos
    debug: true // Ativa logs no console
};

// ========================================
// FUNÇÕES DE INTEGRAÇÃO
// ========================================

/**
 * Envia dados para o Google Sheets com retry automático
 * @param {Object} data - Dados a serem enviados
 * @param {number} retryCount - Contador de tentativas
 * @returns {Promise<Object>} - Resposta do servidor
 */
async function enviarParaGoogleSheets(data, retryCount = 0) {
    try {
        // Adiciona metadados
        data.timestamp = new Date().toISOString();
        data.userAgent = navigator.userAgent;
        data.referrer = document.referrer;
        data.url = window.location.href;
        
        // Log de debug
        if (CONFIG.debug) {
            console.log('📤 Enviando dados:', data);
        }
        
        // Faz a requisição
        const response = await fetch(GOOGLE_SCRIPT_URL, {
            method: 'POST',
            mode: 'no-cors', // Importante para evitar erros de CORS
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        // Como usamos no-cors, não teremos resposta real
        // Assumimos sucesso se não houver erro
        if (CONFIG.debug) {
            console.log('✅ Dados enviados com sucesso!');
        }
        
        // Salva backup local
        salvarBackupLocal(data);
        
        return { success: true, message: 'Dados enviados com sucesso' };
        
    } catch (error) {
        console.error('❌ Erro no envio:', error);
        
        // Tenta novamente se ainda tiver tentativas
        if (retryCount < CONFIG.maxRetries) {
            console.log(`🔄 Tentando novamente... (${retryCount + 1}/${CONFIG.maxRetries})`);
            
            // Aguarda antes de tentar novamente
            await aguardar(CONFIG.retryDelay);
            
            return enviarParaGoogleSheets(data, retryCount + 1);
        }
        
        // Se esgotou as tentativas, salva localmente
        salvarBackupLocal(data);
        
        return { 
            success: false, 
            message: 'Erro no envio, dados salvos localmente',
            error: error.toString()
        };
    }
}

/**
 * Função auxiliar para aguardar
 * @param {number} ms - Milissegundos para aguardar
 */
function aguardar(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Salva backup dos dados no localStorage
 * @param {Object} data - Dados para backup
 */
function salvarBackupLocal(data) {
    try {
        // Recupera backups existentes
        const backups = JSON.parse(localStorage.getItem('backups_pendentes') || '[]');
        
        // Adiciona novo backup
        backups.push({
            ...data,
            backup_timestamp: new Date().toISOString()
        });
        
        // Limita a 50 backups para não sobrecarregar o localStorage
        if (backups.length > 50) {
            backups.shift(); // Remove o mais antigo
        }
        
        // Salva no localStorage
        localStorage.setItem('backups_pendentes', JSON.stringify(backups));
        
        console.log('💾 Backup salvo localmente');
        
    } catch (error) {
        console.error('Erro ao salvar backup:', error);
    }
}

/**
 * Tenta reenviar backups pendentes
 */
async function reenviarBackupsPendentes() {
    try {
        const backups = JSON.parse(localStorage.getItem('backups_pendentes') || '[]');
        
        if (backups.length === 0) {
            console.log('Não há backups pendentes');
            return;
        }
        
        console.log(`📨 Reenviando ${backups.length} backups pendentes...`);
        
        const sucessos = [];
        const falhas = [];
        
        for (const backup of backups) {
            const resultado = await enviarParaGoogleSheets(backup);
            
            if (resultado.success) {
                sucessos.push(backup);
            } else {
                falhas.push(backup);
            }
            
            // Aguarda entre envios para não sobrecarregar
            await aguardar(500);
        }
        
        // Atualiza localStorage apenas com as falhas
        localStorage.setItem('backups_pendentes', JSON.stringify(falhas));
        
        console.log(`✅ ${sucessos.length} backups reenviados com sucesso`);
        console.log(`❌ ${falhas.length} backups falharam`);
        
    } catch (error) {
        console.error('Erro ao reenviar backups:', error);
    }
}

// ========================================
// FUNÇÕES ESPECÍFICAS POR TIPO DE DADOS
// ========================================

/**
 * Envia dados da página de captura inicial (index.html)
 */
async function enviarLeadInicial(formData) {
    const dados = {
        type: 'lead',
        nome: formData.nome,
        whatsapp: formData.whatsapp,
        tipoVeiculo: formData.tipoVeiculo,
        estadoOrigem: formData.estadoOrigem,
        cidadeOrigem: formData.cidadeOrigem,
        estadoDestino: formData.estadoDestino,
        cidadeDestino: formData.cidadeDestino,
        kmConsultado: formData.kmConsultado,
        device: detectarDispositivo(),
        ip: await obterIP()
    };
    
    return enviarParaGoogleSheets(dados);
}

/**
 * Envia propostas da página de cotação (cotacao.html)
 */
async function enviarPropostas(proposalData) {
    const dados = {
        type: 'proposta',
        ...proposalData,
        device: detectarDispositivo()
    };
    
    return enviarParaGoogleSheets(dados);
}

/**
 * Envia rotas favoritas
 */
async function enviarRotasFavoritas(rotasData) {
    const dados = {
        type: 'rotas',
        ...rotasData,
        device: detectarDispositivo()
    };
    
    return enviarParaGoogleSheets(dados);
}

/**
 * Envia análise final (confirmacao.html)
 */
async function enviarAnaliseFinal(analysisData) {
    const dados = {
        type: 'analise',
        ...analysisData,
        device: detectarDispositivo()
    };
    
    return enviarParaGoogleSheets(dados);
}

// ========================================
// FUNÇÕES AUXILIARES
// ========================================

/**
 * Detecta o tipo de dispositivo
 */
function detectarDispositivo() {
    const userAgent = navigator.userAgent;
    
    if (/Mobile|Android|iPhone|iPad|iPod/.test(userAgent)) {
        if (/iPad|Tablet/.test(userAgent)) {
            return 'Tablet';
        }
        return 'Mobile';
    }
    
    return 'Desktop';
}

/**
 * Tenta obter o IP do cliente (usando serviço externo)
 */
async function obterIP() {
    try {
        const response = await fetch('https://api.ipify.org?format=json');
        const data = await response.json();
        return data.ip;
    } catch (error) {
        return 'Não disponível';
    }
}

/**
 * Formata número de WhatsApp para padrão brasileiro
 */
function formatarWhatsApp(numero) {
    // Remove tudo que não é número
    const apenasNumeros = numero.replace(/\D/g, '');
    
    // Adiciona 55 se não tiver
    let numeroFormatado = apenasNumeros;
    if (!numeroFormatado.startsWith('55')) {
        numeroFormatado = '55' + numeroFormatado;
    }
    
    // Adiciona 9 se for celular e não tiver
    if (numeroFormatado.length === 12) {
        const ddd = numeroFormatado.substring(2, 4);
        const numero = numeroFormatado.substring(4);
        if (!numero.startsWith('9')) {
            numeroFormatado = '55' + ddd + '9' + numero;
        }
    }
    
    return numeroFormatado;
}

/**
 * Valida email
 */
function validarEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Valida CPF/CNPJ
 */
function validarDocumento(doc) {
    const apenasNumeros = doc.replace(/\D/g, '');
    
    if (apenasNumeros.length === 11) {
        return validarCPF(apenasNumeros);
    } else if (apenasNumeros.length === 14) {
        return validarCNPJ(apenasNumeros);
    }
    
    return false;
}

function validarCPF(cpf) {
    // Validação básica de CPF
    if (cpf.length !== 11) return false;
    if (/^(\d)\1{10}$/.test(cpf)) return false;
    
    // Cálculo dos dígitos verificadores
    let soma = 0;
    for (let i = 0; i < 9; i++) {
        soma += parseInt(cpf.char(i)) * (10 - i);
    }
    let resto = (soma * 10) % 11;
    if (resto === 10 || resto === 11) resto = 0;
    if (resto !== parseInt(cpf.charAt(9))) return false;
    
    soma = 0;
    for (let i = 0; i < 10; i++) {
        soma += parseInt(cpf.charAt(i)) * (11 - i);
    }
    resto = (soma * 10) % 11;
    if (resto === 10 || resto === 11) resto = 0;
    if (resto !== parseInt(cpf.charAt(10))) return false;
    
    return true;
}

function validarCNPJ(cnpj) {
    // Validação básica de CNPJ
    if (cnpj.length !== 14) return false;
    if (/^(\d)\1{13}$/.test(cnpj)) return false;
    
    // Validação mais complexa omitida por brevidade
    return true;
}

// ========================================
// INICIALIZAÇÃO
// ========================================

/**
 * Inicializa o sistema de integração
 */
function inicializarIntegracao() {
    console.log('🚀 Sistema de integração inicializado');
    
    // Verifica se há backups pendentes
    const backups = JSON.parse(localStorage.getItem('backups_pendentes') || '[]');
    if (backups.length > 0) {
        console.log(`📦 ${backups.length} backups pendentes encontrados`);
        
        // Agenda reenvio para 5 segundos após carregar a página
        setTimeout(() => {
            reenviarBackupsPendentes();
        }, 5000);
    }
    
    // Adiciona listener para quando voltar online
    window.addEventListener('online', () => {
        console.log('🌐 Conexão restaurada, tentando reenviar backups...');
        reenviarBackupsPendentes();
    });
    
    // Adiciona listener para antes de fechar a página
    window.addEventListener('beforeunload', (event) => {
        const backups = JSON.parse(localStorage.getItem('backups_pendentes') || '[]');
        if (backups.length > 0) {
            event.preventDefault();
            event.returnValue = 'Há dados pendentes de envio. Deseja sair mesmo assim?';
        }
    });
}

// ========================================
// EXPORTAÇÃO DE FUNÇÕES
// ========================================

// Torna as funções disponíveis globalmente
window.IntegracaoSheets = {
    enviarParaGoogleSheets,
    enviarLeadInicial,
    enviarPropostas,
    enviarRotasFavoritas,
    enviarAnaliseFinal,
    reenviarBackupsPendentes,
    formatarWhatsApp,
    validarEmail,
    validarDocumento,
    inicializarIntegracao
};

// Inicializa automaticamente quando o DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inicializarIntegracao);
} else {
    inicializarIntegracao();
}

console.log('✨ Integração com Google Sheets carregada com sucesso!');
