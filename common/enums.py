from enum import Enum


class Herramientas(Enum):
    Cypress = 'Cypress'
    Calabash = 'Calabash'
    Puppeteer = 'Puppeteer'
    ADB = 'ADB Nativo'


class TiposAplicacion(Enum):
    Movil = 'Móvil'
    Web = 'Web'


class TiposPruebas(Enum):
    E2E = 'E2E'
    Aleatorias = 'Aleatorias'


class RutasInternas(Enum):
    Cypress = 'cypress/integration'
    Calabash = 'features'
    Puppeteer = 'src/test'
    Mutacion = 'mutants'
