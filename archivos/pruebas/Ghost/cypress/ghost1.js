describe('Ghost UI links redirection', function() {
    it('Goes to site when its link is clicked', function() {
        cy.visit('https://ghost-grupo6.herokuapp.com/ghost/#/signin');
        cy.get('#ember8').click().type("jc.piza@uniandes.edu.co");
        cy.get('#ember10').click().type("tRjX$FapKvGsz5G");
        cy.get('#ember12').contains("Sign in");
        cy.get('#ember12').click();
        cy.get('#ember27').click();
        cy.url().should('eq', 'https://ghost-grupo6.herokuapp.com/ghost/#/site');
    });
    it('Goes to posts when its link is clicked', function() {
        cy.visit('https://ghost-grupo6.herokuapp.com/ghost/#/signin');
        cy.get('#ember8').click().type("jc.piza@uniandes.edu.co");
        cy.get('#ember10').click().type("tRjX$FapKvGsz5G");
        cy.get('#ember12').contains("Sign in");
        cy.get('#ember12').click();
        cy.get('#ember28').click();
        cy.url().should('eq', 'https://ghost-grupo6.herokuapp.com/ghost/#/posts');
    });
    it('Goes to pages when its link is clicked', function() {
        cy.visit('https://ghost-grupo6.herokuapp.com/ghost/#/signin');
        cy.get('#ember8').click().type("jc.piza@uniandes.edu.co");
        cy.get('#ember10').click().type("tRjX$FapKvGsz5G");
        cy.get('#ember12').contains("Sign in");
        cy.get('#ember12').click();
        cy.get('#ember30').click();
        cy.url().should('eq', 'https://ghost-grupo6.herokuapp.com/ghost/#/pages');
    });
});