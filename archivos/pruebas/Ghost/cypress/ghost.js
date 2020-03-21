describe('Login into Ghost', function() {
    it('Login failed with wrong inputs', function() {
        cy.visit('http://ec2-52-54-255-159.compute-1.amazonaws.com/ghost/#/signin');
        cy.get('#ember8').click().type("asd");
        cy.get('#ember10').click().type("asd");
        cy.get('#ember12').contains("Sign in");
        cy.get('#ember12').click();
        cy.get('#ember12').contains("Retry");
        cy.get('.main-error').contains("Please fill out the form to sign in.")
    });
    it('Login failed with invalid inputs', function() {
        cy.visit('http://ec2-52-54-255-159.compute-1.amazonaws.com/ghost/#/signin');
        cy.get('#ember8').click().type("asd@as.asd");
        cy.get('#ember10').click().type("asd");
        cy.get('#ember12').contains("Sign in");
        cy.get('#ember12').click();
        cy.get('#ember12').contains("Sign in");
        cy.get('.main-error').contains("Access denied.")
    });
    it('Login success with correct inputs', function() {
        cy.visit('http://ec2-52-54-255-159.compute-1.amazonaws.com/ghost/#/signin');
        cy.get('#ember8').click().type("jc.piza@uniandes.edu.co");
        cy.get('#ember10').click().type("tRjX$FapKvGsz5G");
        cy.get('#ember12').contains("Sign in");
        cy.get('#ember12').click();
        cy.get('.gh-nav-menu-details-blog').contains("Prueba");
    });
});