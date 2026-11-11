(function () {
  var form = document.getElementById("formulario-solicitacao");
  if (!form) {
    return;
  }

  var lista = document.getElementById("pecas");
  var modelo = document.getElementById("modelo-peca");
  var adicionar = document.getElementById("adicionar-peca");
  var placa = document.getElementById("placa");
  var foraPadrao = document.getElementById("placa_fora_padrao");
  var ajuda = document.getElementById("ajuda-placa");
  var extra = document.getElementById("identificacao-extra");
  var nome = document.getElementById("responsavel_nome");
  var nomes = document.getElementById("nomes-frequentes");
  var limite = document.getElementById("limite-pecas");
  var maximo = 30;
  var chaveNomes = "elite-truck-nomes";

  function linhas() {
    return Array.prototype.slice.call(lista.querySelectorAll("[data-peca]"));
  }

  function numerar() {
    var todas = linhas();
    todas.forEach(function (linha, indice) {
      var titulo = linha.querySelector(".peca-titulo");
      var remover = linha.querySelector("[data-remover]");
      if (titulo) {
        titulo.textContent = "Peça " + (indice + 1);
      }
      if (remover) {
        remover.textContent = todas.length === 1 ? "Limpar" : "Remover";
      }
    });
    todas.forEach(function (linha) {
      var duplicar = linha.querySelector("[data-duplicar]");
      if (duplicar) {
        duplicar.disabled = todas.length >= maximo;
      }
    });
    if (adicionar) {
      adicionar.disabled = todas.length >= maximo;
    }
    if (limite) {
      limite.hidden = todas.length < maximo;
    }
    var contagem = document.getElementById("contagem-pecas");
    if (contagem) {
      contagem.textContent = todas.length === 1 ? "1 peça" : todas.length + " peças";
    }
  }

  function limpar(linha) {
    linha.querySelector("[name='item_descricao']").value = "";
    linha.querySelector("[name='item_observacao']").value = "";
    linha.querySelector("[name='item_quantidade']").value = "1";
    linha.querySelector("[name='item_unidade']").value = "UN";
  }

  if (adicionar && modelo) {
    adicionar.addEventListener("click", function () {
      if (linhas().length >= maximo) {
        return;
      }
      var origem = modelo.content.querySelector("[data-peca]");
      if (!origem) {
        return;
      }
      var nova = origem.cloneNode(true);
      lista.appendChild(nova);
      numerar();
      var campo = nova.querySelector("[name='item_descricao']");
      if (campo) {
        campo.focus();
      }
    });
  }

  lista.addEventListener("click", function (event) {
    var duplicar = event.target.closest("[data-duplicar]");
    if (duplicar) {
      var origem = duplicar.closest("[data-peca]");
      if (!origem || linhas().length >= maximo) {
        return;
      }
      var copia = origem.cloneNode(true);
      origem.after(copia);
      numerar();
      var campo = copia.querySelector("[name='item_descricao']");
      if (campo) {
        campo.focus();
      }
      return;
    }
    var botao = event.target.closest("[data-remover]");
    if (!botao) {
      return;
    }
    var linha = botao.closest("[data-peca]");
    if (!linha) {
      return;
    }
    if (linhas().length === 1) {
      limpar(linha);
      return;
    }
    linha.remove();
    numerar();
  });

  function mascara() {
    if (!placa || foraPadrao.checked) {
      return;
    }
    var bruto = placa.value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 7);
    var mercosul = bruto.length >= 5 && /[A-Z]/.test(bruto.charAt(4));
    if (mercosul || bruto.length <= 3) {
      placa.value = bruto;
      return;
    }
    placa.value = bruto.slice(0, 3) + "-" + bruto.slice(3);
  }

  function atualizarModoPlaca() {
    if (!placa || !foraPadrao) {
      return;
    }
    if (extra) {
      var campoExtra = extra.querySelector("[name='identificacao_adicional']");
      var temExtra = campoExtra && campoExtra.value.trim() !== "";
      extra.hidden = !foraPadrao.checked && !temExtra;
    }
    if (foraPadrao.checked) {
      placa.maxLength = 30;
      placa.placeholder = "Ex.: FROTA 12";
      if (ajuda) {
        ajuda.textContent = "Use a identificação interna, o chassi curto ou outro código do veículo.";
      }
      placa.value = placa.value.toUpperCase().slice(0, 30);
      return;
    }
    placa.maxLength = 8;
    placa.placeholder = "ABC1D23";
    if (ajuda) {
      ajuda.textContent = "Placa antiga (ABC-1234) ou Mercosul (ABC1D23). Se não houver placa nesse padrão, marque a opção abaixo.";
    }
    mascara();
  }

  if (placa) {
    placa.addEventListener("input", function () {
      if (foraPadrao && foraPadrao.checked) {
        placa.value = placa.value.toUpperCase().slice(0, 30);
        return;
      }
      mascara();
    });
  }
  if (foraPadrao) {
    foraPadrao.addEventListener("change", atualizarModoPlaca);
  }
  function lerNomes() {
    try {
      var guardados = JSON.parse(window.localStorage.getItem(chaveNomes) || "[]");
      return Array.isArray(guardados) ? guardados : [];
    } catch (erro) {
      return [];
    }
  }

  function mostrarNomes() {
    if (!nomes) {
      return;
    }
    nomes.innerHTML = "";
    lerNomes().forEach(function (item) {
      var opcao = document.createElement("option");
      opcao.value = item;
      nomes.appendChild(opcao);
    });
  }

  function guardarNome() {
    if (!nome || !window.localStorage) {
      return;
    }
    var texto = nome.value.trim();
    if (texto.length < 3) {
      return;
    }
    var atuais = lerNomes().filter(function (item) {
      return String(item).toLowerCase() !== texto.toLowerCase();
    });
    atuais.unshift(texto);
    window.localStorage.setItem(chaveNomes, JSON.stringify(atuais.slice(0, 8)));
    mostrarNomes();
  }

  if (nome) {
    mostrarNomes();
    nome.addEventListener("change", guardarNome);
  }

  var chavePecas = "elite-truck-pecas";
  var descricoes = document.getElementById("descricoes-frequentes");
  var sugestoes = document.getElementById("sugestoes-pecas");

  function lerPecas() {
    try {
      var guardadas = JSON.parse(window.localStorage.getItem(chavePecas) || "[]");
      return Array.isArray(guardadas) ? guardadas : [];
    } catch (erro) {
      return [];
    }
  }

  function mostrarPecas() {
    var atuais = lerPecas();
    if (descricoes) {
      descricoes.innerHTML = "";
      atuais.forEach(function (item) {
        var opcao = document.createElement("option");
        opcao.value = item;
        descricoes.appendChild(opcao);
      });
    }
    if (!sugestoes) {
      return;
    }
    sugestoes.innerHTML = "";
    atuais.slice(0, 4).forEach(function (item) {
      var botao = document.createElement("button");
      botao.type = "button";
      botao.className = "sugestao-peca";
      botao.textContent = item;
      botao.addEventListener("click", function () {
        var destino = null;
        linhas().forEach(function (linha) {
          var campo = linha.querySelector("[name='item_descricao']");
          if (!destino && campo && !campo.value.trim()) {
            destino = campo;
          }
        });
        if (!destino) {
          var ultima = linhas()[linhas().length - 1];
          destino = ultima ? ultima.querySelector("[name='item_descricao']") : null;
        }
        if (destino) {
          destino.value = item;
          destino.focus();
        }
      });
      sugestoes.appendChild(botao);
    });
  }

  function guardarPecas() {
    if (!window.localStorage) {
      return;
    }
    var atuais = lerPecas();
    form.querySelectorAll("[name='item_descricao']").forEach(function (campo) {
      var texto = campo.value.trim();
      if (texto.length < 3) {
        return;
      }
      atuais = atuais.filter(function (item) {
        return String(item).toLowerCase() !== texto.toLowerCase();
      });
      atuais.unshift(texto);
    });
    window.localStorage.setItem(chavePecas, JSON.stringify(atuais.slice(0, 8)));
    mostrarPecas();
  }

  if (descricoes || sugestoes) {
    mostrarPecas();
  }

  form.addEventListener("submit", function () {
    guardarNome();
    guardarPecas();
  });

  var paineis = Array.prototype.slice.call(form.querySelectorAll("[data-etapa]"));
  var voltar = document.getElementById("passo-voltar");
  var continuar = document.getElementById("passo-continuar");
  var trilha = document.getElementById("trilha-preenchida");
  var botoes = Array.prototype.slice.call(document.querySelectorAll("[data-ir]"));
  var atual = 1;

  function pendencia(etapa) {
    if (etapa === 1) {
      if (!placa || placa.value.trim().length < 2) {
        return { campo: placa, texto: "Informe a placa ou a identificação do veículo." };
      }
      if (!form.querySelector("input[name='tipo_veiculo']:checked")) {
        return { campo: form.querySelector(".grade-tipo"), texto: "Escolha o tipo de veículo." };
      }
      var marca = document.getElementById("marca");
      if (!marca || marca.value.trim().length < 2) {
        return { campo: marca, texto: "Informe a marca." };
      }
      var modelo = document.getElementById("modelo");
      if (!modelo || modelo.value.trim().length < 1) {
        return { campo: modelo, texto: "Informe o modelo." };
      }
    }
    if (etapa === 2) {
      if (!nome || nome.value.trim().length < 3) {
        return { campo: nome, texto: "Informe o nome de quem está pedindo." };
      }
    }
    if (etapa === 3) {
      var alguma = false;
      var cartoes = linhas();
      for (var i = 0; i < cartoes.length; i += 1) {
        var descricao = cartoes[i].querySelector("[name='item_descricao']");
        var quantidade = cartoes[i].querySelector("[name='item_quantidade']");
        if (descricao && descricao.value.trim()) {
          alguma = true;
          if (!quantidade || !quantidade.value.trim()) {
            return { campo: quantidade, texto: "Informe a quantidade desta peça." };
          }
        }
      }
      if (!alguma) {
        var primeiro = cartoes[0] ? cartoes[0].querySelector("[name='item_descricao']") : null;
        return { campo: primeiro, texto: "Informe ao menos uma peça." };
      }
    }
    return null;
  }

  function apontar(problema) {
    var aviso = document.getElementById("aviso-passo");
    if (!aviso) {
      aviso = document.createElement("p");
      aviso.id = "aviso-passo";
      aviso.className = "erro-campo";
      aviso.setAttribute("role", "alert");
    }
    var painel = paineis[atual - 1];
    if (painel) {
      painel.insertBefore(aviso, painel.querySelector(".bloco-titulo").nextSibling);
    }
    aviso.hidden = false;
    aviso.textContent = problema.texto;
    if (problema.campo && typeof problema.campo.focus === "function") {
      problema.campo.focus();
    }
  }

  function mostrar(numero) {
    atual = numero;
    paineis.forEach(function (painel, indice) {
      painel.classList.toggle("ativa", indice + 1 === numero);
    });
    botoes.forEach(function (botao) {
      var etapa = parseInt(botao.getAttribute("data-ir"), 10);
      botao.classList.toggle("atual", etapa === numero);
      botao.classList.toggle("feita", etapa < numero);
      if (etapa === numero) {
        botao.setAttribute("aria-current", "step");
      } else {
        botao.removeAttribute("aria-current");
      }
    });
    if (trilha) {
      trilha.style.width = ((numero / 4) * 100) + "%";
    }
    if (voltar) {
      voltar.hidden = numero === 1;
    }
    if (continuar) {
      continuar.textContent = numero === paineis.length ? "Revisar solicitação" : "Continuar";
    }
    var aviso = document.getElementById("aviso-passo");
    if (aviso) {
      aviso.hidden = true;
    }
    var progresso = document.querySelector(".progresso");
    if (progresso && progresso.scrollIntoView) {
      progresso.scrollIntoView({ block: "start" });
    }
  }

  function ir(destino, validar) {
    destino = Math.max(1, Math.min(paineis.length, destino));
    if (validar && destino > atual) {
      for (var etapa = atual; etapa < destino; etapa += 1) {
        var problema = pendencia(etapa);
        if (problema) {
          mostrar(etapa);
          apontar(problema);
          return;
        }
      }
    }
    if (atual === 3 && destino !== 3) {
      guardarPecas();
    }
    mostrar(destino);
  }

  if (paineis.length && voltar && continuar) {
    form.classList.add("com-passos");
    var inicial = 1;
    for (var indice = 0; indice < paineis.length; indice += 1) {
      if (paineis[indice].querySelector(".erro-campo, .is-invalid")) {
        inicial = indice + 1;
        break;
      }
    }
    if (inicial === 1 && !document.querySelector(".alert-danger")) {
      var pedida = parseInt(new URLSearchParams(window.location.search).get("etapa"), 10);
      if (pedida >= 1 && pedida <= paineis.length) {
        inicial = pedida;
      }
    }
    mostrar(inicial);
    voltar.addEventListener("click", function () {
      ir(atual - 1, false);
    });
    continuar.addEventListener("click", function () {
      if (atual < paineis.length) {
        ir(atual + 1, true);
        return;
      }
      for (var etapa = 1; etapa <= paineis.length; etapa += 1) {
        var problema = pendencia(etapa);
        if (problema) {
          mostrar(etapa);
          apontar(problema);
          return;
        }
      }
      guardarPecas();
      if (typeof form.requestSubmit === "function") {
        form.requestSubmit();
        return;
      }
      form.submit();
    });
    botoes.forEach(function (botao) {
      botao.addEventListener("click", function () {
        ir(parseInt(botao.getAttribute("data-ir"), 10), true);
      });
    });
    var barra = document.querySelector(".barra-passos");
    function encaixarBarra() {
      if (!barra || !window.visualViewport) {
        return;
      }
      var coberta = Math.max(0, window.innerHeight - window.visualViewport.height - window.visualViewport.offsetTop);
      barra.style.bottom = coberta + "px";
    }
    if (window.visualViewport) {
      window.visualViewport.addEventListener("resize", encaixarBarra);
      window.visualViewport.addEventListener("scroll", encaixarBarra);
    }
    form.addEventListener("focusin", function (event) {
      window.setTimeout(function () {
        if (event.target && event.target.scrollIntoView) {
          event.target.scrollIntoView({ block: "center" });
        }
      }, 280);
    });
  }

  atualizarModoPlaca();
  numerar();
})();
