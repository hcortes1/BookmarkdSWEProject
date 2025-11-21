// friends graph hover effects
document.addEventListener('DOMContentLoaded', function() {
    // wait for cytoscape to be ready
    const checkCytoscape = setInterval(function() {
        const cyElement = document.getElementById('friends-network');
        if (cyElement && cyElement._cyreg && cyElement._cyreg.cy) {
            const cy = cyElement._cyreg.cy;
            
            // add hover effects
            cy.on('mouseover', 'node', function(evt) {
                const node = evt.target;
                const nodeType = node.data('type');
                
                // Set hover label data field
                node.data('hoverLabel', node.data('label'));
                
                let hoverSize = 75;
                if (nodeType === 'center') {
                    hoverSize = 95;
                } else if (nodeType === 'friend_of_friend') {
                    hoverSize = 40;
                }
                
                node.animate({
                    style: {
                        'width': hoverSize + 'px',
                        'height': hoverSize + 'px'
                    },
                    duration: 200
                });
            });
            
            cy.on('mouseout', 'node', function(evt) {
                const node = evt.target;
                const nodeType = node.data('type');
                
                // Clear hover label data field
                node.data('hoverLabel', '');
                
                let baseSize = 60;
                if (nodeType === 'center') {
                    baseSize = 80;
                } else if (nodeType === 'friend_of_friend') {
                    baseSize = 30;
                }
                
                node.animate({
                    style: {
                        'width': baseSize + 'px',
                        'height': baseSize + 'px'
                    },
                    duration: 200
                });
            });
            
            clearInterval(checkCytoscape);
        }
    }, 100);
});
