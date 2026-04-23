document.addEventListener('DOMContentLoaded', function() {
    const showKeyBtn = document.getElementById('showKeyBtn');
    const keyBox = document.getElementById('keyBox');
    const keyUrl = document.getElementById('keyUrl');
    const copyBtn = document.getElementById('copyBtn');
    
    showKeyBtn.addEventListener('click', function() {
        keyBox.style.display = 'block';
        showKeyBtn.style.display = 'none';
        keyUrl.select();
    });
 
    copyBtn.addEventListener('click', function() {
        navigator.clipboard.writeText(keyUrl.value).then(function() {
            alert('Ключ скопирован');
        });
    });
});