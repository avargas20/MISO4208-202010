describe('Your WebApp under monkeys', function() {
    it('visits your WebApp and survives monkeys', function() {
        cy.visit('-urlToken-');
        randomEvent(100);
    })
})

function randomEvent(monkeysQty) {
    var monkeysLeft = monkeysQty;
    if (monkeysLeft > 0) {
        console.log("--- Quedan " + monkeysLeft + " Monkeys ---");
        monkeysLeft = monkeysLeft - 1;
        callRandomFunction(monkeysLeft);
    } else {
        console.log("--- Monkey Testing terminado ---");
    }
}

function callRandomFunction(monkeysLeft) {
    switch (getRandomInt(0, 3)) {
        case 0:
            console.log("Llamando clickRandomLink")
            clickRandomLink(monkeysLeft);
            break;
        case 1:
            console.log("Llamando fillRandomField")
            fillRandomField(monkeysLeft);
            break;
        case 2:
            console.log("Llamando selectRandomCombo")
            selectRandomCombo(monkeysLeft);
            break;
        case 3:
            console.log("Llamando clickRandomButton")
            clickRandomButton(monkeysLeft);
            break;
    }
}

function getRandomInt(min, max) {
    min = Math.ceil(min);
    max = Math.floor(max);
    return Math.floor(Math.random() * (max - min)) + min;
};

function clickRandomLink(monkeysLeft) {
    cy.get("body").then($body => {
        if ($body.find('a').length > 0) {
            cy.get('a').then($links => {
                var randomLink = $links.get(getRandomInt(0, $links.length));
                if (!Cypress.dom.isHidden(randomLink)) {
                    cy.wrap(randomLink).click({ force: true });
                    cy.wait(1000);
                    randomEvent(monkeysLeft);
                } else {
                    cy.wait(1000);
                    randomEvent(monkeysLeft);
                }
            });
        } else {
            cy.wait(1000);
            randomEvent(monkeysLeft);
        }
    });
}

function fillRandomField(monkeysLeft) {
    cy.get("body").then($body => {
        if ($body.find('input').length > 0) {
            cy.get('input').then($inputs => {
                var randomInput = $inputs.get(getRandomInt(0, $inputs.length));
                if (!Cypress.dom.isHidden(randomInput)) {
                    cy.get(randomInput).type("text testing", { force: true });
                    cy.wait(1000);
                    randomEvent(monkeysLeft);
                } else {
                    cy.wait(1000);
                    randomEvent(monkeysLeft);
                }
            });
        } else {
            cy.wait(1000);
            randomEvent(monkeysLeft);
        }
    });
}

function selectRandomCombo(monkeysLeft) {
    cy.get("body").then($body => {
        if ($body.find('select').length > 0) {
            cy.get('select').then($combos => {
                var randomCombo = $combos.get(getRandomInt(0, $combos.length));
                if (!Cypress.dom.isHidden(randomCombo)) {
                    cy.get(randomCombo).then($combos => {
                        var options = $combos.find('option')
                        console.log(options)
                        var index = getRandomInt(0, options.length);
                        if (!options[index].disabled) {
                            console.log("Clickeando " + options[index].value)
                            cy.get(randomCombo).select(options[index].value);
                            cy.wait(1000);
                            randomEvent(monkeysLeft);
                        } else {
                            console.log("Saltando " + options[index].value);
                            cy.wait(1000);
                            randomEvent(monkeysLeft);
                        }
                    });
                } else {
                    cy.wait(1000);
                    randomEvent(monkeysLeft);
                }
            });
        } else {
            cy.wait(1000);
            randomEvent(monkeysLeft);
        }
    });
}

function clickRandomButton(monkeysLeft) {
    cy.get("body").then($body => {
        if ($body.find('button').length > 0) {
            cy.get('button').then($button => {
                var randomButton = $button.get(getRandomInt(0, $button.length));
                if (!Cypress.dom.isHidden(randomButton)) {
                    cy.wrap(randomButton).click({ force: true });
                    cy.wait(1000);
                    randomEvent(monkeysLeft);
                } else {
                    cy.wait(1000);
                    randomEvent(monkeysLeft);
                }
            });
        } else {
            cy.wait(1000);
            randomEvent(monkeysLeft);
        }
    });
}