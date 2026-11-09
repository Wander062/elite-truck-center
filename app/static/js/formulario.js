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
  var limite = document.getElementById("limite-pecas");
  var maximo = 30;

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
    if (adicionar) {
      adicionar.disabled = todas.length >= maximo;
    }
    if (limite) {
      limite.hidden = todas.length < maximo;
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
  atualizarModoPlaca();
  numerar();
})();
