function validateInput(input) {
    // Supprime tous les caractères non numériques sauf les espaces
    input.value = input.value.replace(/[^\d\s]/g, '');
  
    // Supprime les espaces existants
    let num = input.value.replace(/\s/g, '');
  
    // Ajoute des espaces entre les groupes de 3 chiffres
    input.value = num.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  }