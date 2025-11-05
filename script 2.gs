/**
 * Google Apps Script para Sistema de Captação de Leads - Anderson Enside Madeiras
 * 
 * INSTRUÇÕES DE CONFIGURAÇÃO:
 * 1. Crie uma nova planilha no Google Sheets
 * 2. Vá em Extensões > Apps Script
 * 3. Delete o código padrão e cole este código
 * 4. Clique em Salvar (ícone de disquete)
 * 5. Clique em Implantar > Nova implantação
 * 6. Escolha tipo: Aplicativo Web
 * 7. Descrição: API Captação de Leads
 * 8. Executar como: Eu
 * 9. Quem pode acessar: Qualquer pessoa
 * 10. Clique em Implantar
 * 11. Copie a URL do Web App
 * 12. Autorize o script quando solicitado
 */

// IDs das planilhas - SUBSTITUA PELOS SEUS IDs REAIS
const SPREADSHEET_ID = 'SEU_ID_DA_PLANILHA_AQUI'; // Cole o ID da sua planilha aqui

// Nomes das abas (sheets)
const SHEET_NAMES = {
  LEADS: 'Leads Captura',
  PROPOSTAS: 'Propostas Detalhadas',
  ROTAS_FAVORITAS: 'Rotas Favoritas',
  ANALISE_FINAL: 'Análise Final',
  URGENTES: 'Fretes Urgentes'
};

/**
 * Função doPost - Recebe requisições POST do formulário
 */
function doPost(e) {
  try {
    // Parse do JSON recebido
    const data = JSON.parse(e.postData.contents);
    
    // Identifica o tipo de requisição
    const requestType = data.type || 'lead';
    
    let result;
    switch(requestType) {
      case 'lead':
        result = salvarLead(data);
        break;
      case 'proposta':
        result = salvarProposta(data);
        break;
      case 'rotas':
        result = salvarRotasFavoritas(data);
        break;
      case 'analise':
        result = salvarAnaliseFinal(data);
        break;
      default:
        result = { success: false, message: 'Tipo de requisição inválido' };
    }
    
    // Retorna resposta JSON
    return ContentService
      .createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    return ContentService
      .createTextOutput(JSON.stringify({
        success: false,
        message: 'Erro ao processar requisição',
        error: error.toString()
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Função doGet - Permite testar se o script está funcionando
 */
function doGet(e) {
  return ContentService
    .createTextOutput(JSON.stringify({
      success: true,
      message: 'API Anderson Enside Madeiras está funcionando!',
      timestamp: new Date().toISOString()
    }))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Salva lead inicial (página 1)
 */
function salvarLead(data) {
  try {
    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    let sheet = ss.getSheetByName(SHEET_NAMES.LEADS);
    
    // Cria a aba se não existir
    if (!sheet) {
      sheet = ss.insertSheet(SHEET_NAMES.LEADS);
      // Adiciona cabeçalhos
      sheet.getRange(1, 1, 1, 11).setValues([[
        'Timestamp',
        'WhatsApp',
        'Nome',
        'Tipo Veículo',
        'Estado Origem',
        'Cidade Origem',
        'Estado Destino',
        'Cidade Destino',
        'KM Consultado',
        'Device',
        'IP'
      ]]);
      
      // Formata cabeçalhos
      sheet.getRange(1, 1, 1, 11)
        .setBackground('#1F2937')
        .setFontColor('#FFFFFF')
        .setFontWeight('bold');
    }
    
    // Adiciona nova linha
    sheet.appendRow([
      new Date().toLocaleString('pt-BR'),
      data.whatsapp || '',
      data.nome || '',
      data.tipoVeiculo || '',
      data.estadoOrigem || '',
      data.cidadeOrigem || '',
      data.estadoDestino || '',
      data.cidadeDestino || '',
      data.kmConsultado || 0,
      data.device || '',
      data.ip || ''
    ]);
    
    return { 
      success: true, 
      message: 'Lead salvo com sucesso',
      id: Utilities.getUuid()
    };
    
  } catch (error) {
    return { 
      success: false, 
      message: 'Erro ao salvar lead',
      error: error.toString()
    };
  }
}

/**
 * Salva propostas detalhadas (página 2)
 */
function salvarProposta(data) {
  try {
    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    let sheet = ss.getSheetByName(SHEET_NAMES.PROPOSTAS);
    
    // Cria a aba se não existir
    if (!sheet) {
      sheet = ss.insertSheet(SHEET_NAMES.PROPOSTAS);
      // Adiciona cabeçalhos
      sheet.getRange(1, 1, 1, 13).setValues([[
        'Timestamp',
        'WhatsApp',
        'Nome',
        'Rota',
        'KM',
        'Tipo Carga',
        'Toneladas',
        'Preço Sugerido',
        'Proposta Motorista',
        'Diferença R$',
        'Diferença %',
        'Valor/KM',
        'Valor/Ton'
      ]]);
      
      // Formata cabeçalhos
      sheet.getRange(1, 1, 1, 13)
        .setBackground('#DC2626')
        .setFontColor('#FFFFFF')
        .setFontWeight('bold');
    }
    
    // Processa cada proposta
    if (data.propostas && Array.isArray(data.propostas)) {
      data.propostas.forEach(proposta => {
        const propostaValor = parseFloat(proposta.proposta) || 0;
        const sugeridoValor = parseFloat(proposta.precoSugerido) || 0;
        const km = parseInt(proposta.km) || 0;
        const toneladas = parseInt(proposta.toneladas) || 0;
        
        const diferenca = propostaValor - sugeridoValor;
        const diferencaPercent = sugeridoValor ? ((diferenca / sugeridoValor) * 100).toFixed(2) : 0;
        const valorPorKm = km ? (propostaValor / km).toFixed(2) : 0;
        const valorPorTon = toneladas ? (propostaValor / toneladas).toFixed(2) : 0;
        
        sheet.appendRow([
          new Date().toLocaleString('pt-BR'),
          data.whatsapp || '',
          data.nome || '',
          proposta.rota || '',
          km,
          proposta.tipoCarga || '',
          toneladas,
          sugeridoValor,
          propostaValor,
          diferenca.toFixed(2),
          diferencaPercent + '%',
          valorPorKm,
          valorPorTon
        ]);
      });
    }
    
    // Salva fretes urgentes em aba separada
    if (data.urgentes && Array.isArray(data.urgentes)) {
      salvarFretesUrgentes(data);
    }
    
    return { 
      success: true, 
      message: 'Propostas salvas com sucesso'
    };
    
  } catch (error) {
    return { 
      success: false, 
      message: 'Erro ao salvar propostas',
      error: error.toString()
    };
  }
}

/**
 * Salva fretes urgentes
 */
function salvarFretesUrgentes(data) {
  try {
    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    let sheet = ss.getSheetByName(SHEET_NAMES.URGENTES);
    
    if (!sheet) {
      sheet = ss.insertSheet(SHEET_NAMES.URGENTES);
      sheet.getRange(1, 1, 1, 6).setValues([[
        'Timestamp',
        'WhatsApp',
        'Nome',
        'Rota',
        'Proposta',
        'Status'
      ]]);
      
      sheet.getRange(1, 1, 1, 6)
        .setBackground('#F59E0B')
        .setFontColor('#FFFFFF')
        .setFontWeight('bold');
    }
    
    data.urgentes.forEach(urgente => {
      sheet.appendRow([
        new Date().toLocaleString('pt-BR'),
        data.whatsapp || '',
        data.nome || '',
        urgente.rota || '',
        urgente.proposta || '',
        'URGENTE'
      ]);
    });
    
  } catch (error) {
    console.error('Erro ao salvar fretes urgentes:', error);
  }
}

/**
 * Salva rotas favoritas
 */
function salvarRotasFavoritas(data) {
  try {
    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    let sheet = ss.getSheetByName(SHEET_NAMES.ROTAS_FAVORITAS);
    
    if (!sheet) {
      sheet = ss.insertSheet(SHEET_NAMES.ROTAS_FAVORITAS);
      sheet.getRange(1, 1, 1, 9).setValues([[
        'Timestamp',
        'WhatsApp',
        'Nome',
        'Rota Favorita 1',
        'Preço Habitual 1',
        'Rota Favorita 2',
        'Preço Habitual 2',
        'Fretes/Mês',
        'Perfil'
      ]]);
      
      sheet.getRange(1, 1, 1, 9)
        .setBackground('#10B981')
        .setFontColor('#FFFFFF')
        .setFontWeight('bold');
    }
    
    const rota1 = data.rotasFavoritas && data.rotasFavoritas[0] ? data.rotasFavoritas[0] : {};
    const rota2 = data.rotasFavoritas && data.rotasFavoritas[1] ? data.rotasFavoritas[1] : {};
    
    sheet.appendRow([
      new Date().toLocaleString('pt-BR'),
      data.whatsapp || '',
      data.nome || '',
      rota1.rota || '',
      rota1.preco || '',
      rota2.rota || '',
      rota2.preco || '',
      data.fretesMes || '',
      data.perfil || ''
    ]);
    
    return { 
      success: true, 
      message: 'Rotas favoritas salvas com sucesso'
    };
    
  } catch (error) {
    return { 
      success: false, 
      message: 'Erro ao salvar rotas favoritas',
      error: error.toString()
    };
  }
}

/**
 * Salva análise final (página 3)
 */
function salvarAnaliseFinal(data) {
  try {
    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    let sheet = ss.getSheetByName(SHEET_NAMES.ANALISE_FINAL);
    
    if (!sheet) {
      sheet = ss.insertSheet(SHEET_NAMES.ANALISE_FINAL);
      sheet.getRange(1, 1, 1, 8).setValues([[
        'Timestamp',
        'WhatsApp',
        'Nome',
        'Total Propostas',
        'Valor Total Proposto',
        'Status Geral',
        'Próximo Contato',
        'Observações'
      ]]);
      
      sheet.getRange(1, 1, 1, 8)
        .setBackground('#3B82F6')
        .setFontColor('#FFFFFF')
        .setFontWeight('bold');
    }
    
    // Calcula totais
    let totalPropostas = 0;
    let valorTotal = 0;
    
    if (data.propostas && Array.isArray(data.propostas)) {
      totalPropostas = data.propostas.length;
      valorTotal = data.propostas.reduce((sum, p) => sum + (parseFloat(p.proposta) || 0), 0);
    }
    
    sheet.appendRow([
      new Date().toLocaleString('pt-BR'),
      data.whatsapp || '',
      data.nome || '',
      totalPropostas,
      valorTotal.toFixed(2),
      'Aguardando Análise',
      'Em 15 minutos',
      data.observacoes || 'Lead qualificado via sistema web'
    ]);
    
    // Envia notificação por email (opcional)
    enviarNotificacao(data);
    
    return { 
      success: true, 
      message: 'Análise final salva com sucesso'
    };
    
  } catch (error) {
    return { 
      success: false, 
      message: 'Erro ao salvar análise final',
      error: error.toString()
    };
  }
}

/**
 * Envia notificação por email (opcional)
 */
function enviarNotificacao(data) {
  try {
    const emailDestino = 'anderson@ensideanderson.com'; // SUBSTITUA PELO SEU EMAIL
    const assunto = `Nova Proposta de Frete - ${data.nome || 'Cliente'}`;
    
    let corpo = `
      <h2>Nova Proposta Recebida!</h2>
      <p><strong>Nome:</strong> ${data.nome || 'Não informado'}</p>
      <p><strong>WhatsApp:</strong> ${data.whatsapp || 'Não informado'}</p>
      <p><strong>Tipo de Veículo:</strong> ${data.tipoVeiculo || 'Não informado'}</p>
      <p><strong>Perfil:</strong> ${data.perfil || 'Não informado'}</p>
      <p><strong>Fretes/Mês:</strong> ${data.fretesMes || 'Não informado'}</p>
      
      <h3>Propostas Realizadas:</h3>
      <ul>
    `;
    
    if (data.propostas && Array.isArray(data.propostas)) {
      data.propostas.forEach(proposta => {
        corpo += `<li>${proposta.rota}: R$ ${proposta.proposta}</li>`;
      });
    }
    
    corpo += `
      </ul>
      
      <p><strong>Acesse a planilha para mais detalhes:</strong></p>
      <p><a href="https://docs.google.com/spreadsheets/d/${SPREADSHEET_ID}">Abrir Planilha</a></p>
    `;
    
    // Descomente a linha abaixo para ativar o envio de email
    // MailApp.sendEmail(emailDestino, assunto, '', { htmlBody: corpo });
    
  } catch (error) {
    console.error('Erro ao enviar notificação:', error);
  }
}

/**
 * Função para criar todas as abas necessárias
 * Execute esta função uma vez para preparar a planilha
 */
function criarEstruturaPlanilha() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  
  // Cria aba Leads Captura
  if (!ss.getSheetByName(SHEET_NAMES.LEADS)) {
    const leadsSheet = ss.insertSheet(SHEET_NAMES.LEADS);
    leadsSheet.getRange(1, 1, 1, 11).setValues([[
      'Timestamp', 'WhatsApp', 'Nome', 'Tipo Veículo', 'Estado Origem',
      'Cidade Origem', 'Estado Destino', 'Cidade Destino', 'KM Consultado',
      'Device', 'IP'
    ]]);
    leadsSheet.getRange(1, 1, 1, 11)
      .setBackground('#1F2937')
      .setFontColor('#FFFFFF')
      .setFontWeight('bold');
    leadsSheet.setFrozenRows(1);
  }
  
  // Cria aba Propostas Detalhadas
  if (!ss.getSheetByName(SHEET_NAMES.PROPOSTAS)) {
    const propostasSheet = ss.insertSheet(SHEET_NAMES.PROPOSTAS);
    propostasSheet.getRange(1, 1, 1, 13).setValues([[
      'Timestamp', 'WhatsApp', 'Nome', 'Rota', 'KM', 'Tipo Carga',
      'Toneladas', 'Preço Sugerido', 'Proposta Motorista', 'Diferença R$',
      'Diferença %', 'Valor/KM', 'Valor/Ton'
    ]]);
    propostasSheet.getRange(1, 1, 1, 13)
      .setBackground('#DC2626')
      .setFontColor('#FFFFFF')
      .setFontWeight('bold');
    propostasSheet.setFrozenRows(1);
  }
  
  // Cria aba Rotas Favoritas
  if (!ss.getSheetByName(SHEET_NAMES.ROTAS_FAVORITAS)) {
    const rotasSheet = ss.insertSheet(SHEET_NAMES.ROTAS_FAVORITAS);
    rotasSheet.getRange(1, 1, 1, 9).setValues([[
      'Timestamp', 'WhatsApp', 'Nome', 'Rota Favorita 1', 'Preço Habitual 1',
      'Rota Favorita 2', 'Preço Habitual 2', 'Fretes/Mês', 'Perfil'
    ]]);
    rotasSheet.getRange(1, 1, 1, 9)
      .setBackground('#10B981')
      .setFontColor('#FFFFFF')
      .setFontWeight('bold');
    rotasSheet.setFrozenRows(1);
  }
  
  // Cria aba Análise Final
  if (!ss.getSheetByName(SHEET_NAMES.ANALISE_FINAL)) {
    const analiseSheet = ss.insertSheet(SHEET_NAMES.ANALISE_FINAL);
    analiseSheet.getRange(1, 1, 1, 8).setValues([[
      'Timestamp', 'WhatsApp', 'Nome', 'Total Propostas', 'Valor Total Proposto',
      'Status Geral', 'Próximo Contato', 'Observações'
    ]]);
    analiseSheet.getRange(1, 1, 1, 8)
      .setBackground('#3B82F6')
      .setFontColor('#FFFFFF')
      .setFontWeight('bold');
    analiseSheet.setFrozenRows(1);
  }
  
  // Cria aba Fretes Urgentes
  if (!ss.getSheetByName(SHEET_NAMES.URGENTES)) {
    const urgentesSheet = ss.insertSheet(SHEET_NAMES.URGENTES);
    urgentesSheet.getRange(1, 1, 1, 6).setValues([[
      'Timestamp', 'WhatsApp', 'Nome', 'Rota', 'Proposta', 'Status'
    ]]);
    urgentesSheet.getRange(1, 1, 1, 6)
      .setBackground('#F59E0B')
      .setFontColor('#FFFFFF')
      .setFontWeight('bold');
    urgentesSheet.setFrozenRows(1);
  }
  
  return 'Estrutura da planilha criada com sucesso!';
}

/**
 * Função de teste - Execute para verificar se está funcionando
 */
function testarScript() {
  const testData = {
    type: 'lead',
    nome: 'Teste Anderson',
    whatsapp: '17991234567',
    tipoVeiculo: 'Carreta LS',
    estadoOrigem: 'SP',
    cidadeOrigem: 'Votuporanga',
    estadoDestino: 'PR',
    cidadeDestino: 'Curitiba',
    kmConsultado: 750,
    device: 'Desktop',
    ip: '192.168.1.1'
  };
  
  const result = salvarLead(testData);
  console.log(result);
  return result;
}
