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
                const isCenter = node.data('type') === 'center';
                
                // Set hover label data field
                node.data('hoverLabel', node.data('label'));
                
                node.animate({
                    style: {
                        'width': isCenter ? '95px' : '75px',
                        'height': isCenter ? '95px' : '75px'
                    },
                    duration: 200
                });
            });
            
            cy.on('mouseout', 'node', function(evt) {
                const node = evt.target;
                const isCenter = node.data('type') === 'center';
                
                // Clear hover label data field
                node.data('hoverLabel', '');
                
                node.animate({
                    style: {
                        'width': isCenter ? '80px' : '60px',
                        'height': isCenter ? '80px' : '60px'
                    },
                    duration: 200
                });
            });
            
            clearInterval(checkCytoscape);
        }
    }, 100);
});
