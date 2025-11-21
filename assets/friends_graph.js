// friends graph hover effects
document.addEventListener('DOMContentLoaded', function() {
    // Use MutationObserver to watch for the friends-network element being added
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.id === 'friends-network' || (node.querySelector && node.querySelector('#friends-network'))) {
                    attachHoverEffects();
                }
            });
        });
    });

    observer.observe(document.body, { childList: true, subtree: true });

    // Also try to attach immediately in case it's already there
    attachHoverEffects();

    function attachHoverEffects() {
        const cyElement = document.getElementById('friends-network');
        if (cyElement && cyElement._cyreg && cyElement._cyreg.cy && !cyElement.hasAttribute('data-hover-attached')) {
            const cy = cyElement._cyreg.cy;
            
            // Mark as attached
            cyElement.setAttribute('data-hover-attached', 'true');
            
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
                    baseSize = 25;
                }
                
                node.animate({
                    style: {
                        'width': baseSize + 'px',
                        'height': baseSize + 'px'
                    },
                    duration: 200
                });
            });
        }
    }
});
