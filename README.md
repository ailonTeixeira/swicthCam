💡 Sistema Inteligente de Gestão e Economia de Energia com Validação de Consumo

Uma solução de automação que desliga aparelhos quando um ambiente está vazio e mede o consumo em tempo real para validar e quantificar a economia de energia.

![alt text](https://img.shields.io/badge/propósito-gestão%20energética-lightgreen)


![alt text](https://img.shields.io/badge/tecnologia-Python%20%7C%20Flask%20%7C%20ESP32-blue)


📖 Sumário

    O Problema Resolvido

    Arquitetura de Ciclo Fechado

    🚀 Funcionalidades Principais

    🛠️ Componentes e Tecnologias

    ⚙️ O Ciclo Completo: Detecção, Ação e Medição

    🎯 Conclusão do Projeto
    

🎯 O Problema Resolvido

O desperdício de energia com aparelhos ligados em salas vazias é um desafio comum. No entanto, além de simplesmente desligá-los, é crucial quantificar a economia gerada e validar que a automação está funcionando corretamente.

Este projeto oferece uma solução completa que não só atua para economizar energia, mas também monitora o consumo elétrico para fornecer dados concretos sobre seu impacto, transformando uma ideia de automação em uma ferramenta de gestão energética.

🏛️ Arquitetura de Ciclo Fechado

O sistema é composto por múltiplos nós que trabalham em conjunto para criar um ciclo de controle e verificação:

    Nó de Detecção e Controle (ESP32-CAM):

        Função: Os "olhos" e as "mãos" do sistema.

        Responsabilidades: Fornecer um fluxo de vídeo para a detecção de presença e acionar um relé para controlar fisicamente o aparelho (luz, ar-condicionado, etc.).

    Nó de Monitoramento Energético (ESP32 + SCT-013):

        Função: O "medidor" que valida os resultados.

        Responsabilidades: Medir continuamente a corrente elétrica que passa pelo aparelho e enviar esses dados para o servidor, permitindo a verificação do consumo.

    Servidor Central (Python com Flask):

        Função: O "cérebro" que orquestra todo o processo.

        Responsabilidades: Processar as imagens para detectar presença, tomar decisões de controle, receber os dados de consumo e servir a interface web.

    Interface Web (Painel de Controle):

        Função: O centro de comando e visualização para o usuário.

        Responsabilidades: Exibir o feed de vídeo, permitir controle manual e, potencialmente, exibir os dados de consumo em tempo real.



🚀 Funcionalidades Principais

    Economia de Energia Automatizada: Desliga aparelhos de forma inteligente com base na ausência de pessoas.

    Monitoramento de Consumo em Tempo Real: Utiliza um sensor de corrente (SCT-013) para medir e relatar o consumo elétrico do aparelho controlado.

    Validação da Economia: Fornece dados concretos que provam que a ação de desligamento resultou em uma redução real do consumo.

    Detecção de Presença por Visão Computacional: Usa OpenCV para analisar o vídeo e inferir a presença humana.

    Painel de Controle Centralizado: Oferece uma interface web com login para visualização e controle manual.


🛠️ Componentes e Tecnologias
Hardware

    Servidor: Computador ou Raspberry Pi.

    Nó de Detecção: Módulo ESP32-CAM.

    Nó de Medição: Módulo ESP32 com sensor de corrente não invasivo SCT-013.

    Atuador: Módulo Relé.

Software e Bibliotecas

    Backend (Servidor Central):

        Linguagem: Python

        Framework: Flask

        Visão Computacional: OpenCV

    Frontend (Interface Web):

        HTML5, CSS3, Bootstrap, jQuery

    Firmware (ESP32):

        Arduino Core para ESP32, WiFi.h, esp_camera.h, EmonLib.h


⚙️ O Ciclo Completo: Detecção, Ação e Medição

    Detecção de Presença: O servidor Flask solicita imagens da ESP32-CAM e, usando OpenCV, analisa se o ambiente está ocupado ou vazio.

    Ação de Controle:

        Ambiente Vazio: Se o movimento cessa por um período definido, o servidor envia um comando "OFF" para a ESP32-CAM, que usa o relé para desligar o aparelho.

        Ambiente Ocupado: Ao detectar movimento, o servidor envia um comando "ON" para reativar o aparelho.

    Medição e Validação (O Diferencial):

        Em paralelo, o segundo ESP32, com o sensor SCT-013 conectado ao cabo de alimentação do aparelho, mede a corrente elétrica (Irms).

        A cada poucos segundos, ele envia esses dados de consumo para um endpoint no servidor Flask.

        Isso permite que o sistema confirme que o comando "OFF" realmente zerou o consumo e quantifique os kWh economizados ao longo do tempo.

    Interface com o Usuário: O usuário pode monitorar o feed da câmera e anular a automação a qualquer momento através do painel web, que também pode ser expandido para exibir gráficos de consumo em tempo real.

![diagramaElátricoSwitchCam](https://github.com/user-attachments/assets/94aa683e-a6fd-4b38-8673-03bd22f60609)
    

🎯 Conclusão do Projeto

Este projeto implementa com sucesso um sistema de gestão de energia de ciclo fechado. Ele não apenas executa ações inteligentes para reduzir o desperdício, mas também valida e quantifica seus próprios resultados através de medição contínua. Essa abordagem transforma uma simples automação em uma ferramenta de engenharia robusta, ideal para aplicações que exigem prova de eficiência e análise de dados para otimização contínua do consumo energético.
