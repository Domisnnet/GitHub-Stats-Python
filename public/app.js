document.getElementById('github-form').addEventListener('submit', function(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    if (!username) {
        alert('Por favor, insira um nome de usuário do GitHub.');
        return;
    }

    const theme = document.getElementById('theme-selector').value;
    const statsContainer = document.getElementById('stats-container');
    
    // UI: Limpa e exibe skeleton
    statsContainer.innerHTML = ''; 
    const skeleton = document.createElement('div');
    skeleton.className = 'skeleton-loader';
    statsContainer.appendChild(skeleton);

    // UX: Cache busting para garantir atualização em tempo real
    const timestamp = new Date().getTime();
    const dashboardUrl = `https://us-central1-github-stats-68157678-42e04.cloudfunctions.net/statsSvg?username=${username}&theme=${theme}&t=${timestamp}`;
    
    const dashboardImg = new Image();
    dashboardImg.src = dashboardUrl;
    dashboardImg.alt = 'GitHub Dashboard';
    dashboardImg.className = 'stats-image'; // Garante o estilo CSS

    dashboardImg.onload = function() {
        statsContainer.innerHTML = '';
        statsContainer.appendChild(dashboardImg);
    };

    dashboardImg.onerror = function() {
        statsContainer.innerHTML = '<p class="error-message">Erro ao gerar as estatísticas. Verifique o nome de usuário ou tente novamente mais tarde.</p>';
    };
});