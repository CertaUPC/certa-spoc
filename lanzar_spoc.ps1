# Lanza la corrida definitiva de la prueba de concepto, desacoplada de la
# consola, y con ella el vigilante de saldo.
#
# Va desacoplada porque este equipo recicla procesos cuando escasea la memoria,
# y cada muerte costaba repetir consultas ya pagadas. Con --resume lo ya medido
# no se vuelve a cobrar, de modo que una interrupcion cuesta tiempo pero no
# dinero.

$ErrorActionPreference = "Stop"

$raiz      = "D:\CHRISTOPHER\Universidad\Tesis\certa"
$proyecto  = "$raiz\codigo\certa-backend-api"
$python    = "$proyecto\venv\Scripts\python.exe"
$ejecucion = "75aa891c-4e35-4ca8-84bf-7153fd3a7d48"
$piso      = "1.00"

$argumentos = @(
    "-u", "-m", "src.cli", "compare", $ejecucion,
    "--model", "anthropic/claude-opus-5",
    "--model", "google/gemini-3.8-flash",
    "--model", "qwen/qwen3.8-27b",
    "--batch-size", "100",
    "--repetitions", "3",
    "--max-queries", "140",
    "--resume",
    "--out-dir", "$raiz\spoc"
)

$corrida = Start-Process -FilePath $python -ArgumentList $argumentos `
    -WorkingDirectory $proyecto `
    -RedirectStandardOutput "$raiz\spoc-corrida.log" `
    -RedirectStandardError  "$raiz\spoc-corrida.log.err" `
    -WindowStyle Hidden -PassThru

$corrida.Id | Out-File -FilePath "$raiz\spoc-pid.txt" -Encoding ascii
Write-Output "corrida lanzada, PID $($corrida.Id)"

# El guardia del dominio limita por numero de consultas, que es lo unico que
# puede conocer sin salir del sistema. El saldo real de la cuenta es otra cosa,
# y es lo que de verdad se agota.
$vigilante = Start-Process -FilePath $python -ArgumentList @(
        "-u", "tools\budget_watchdog.py",
        "--pid", $corrida.Id,
        "--piso", $piso,
        "--cada", "180",
        "--log", "$raiz\spoc-saldo.log"
    ) -WorkingDirectory $proyecto `
      -RedirectStandardOutput "$raiz\spoc-vigilante.log" `
      -RedirectStandardError  "$raiz\spoc-vigilante.log.err" `
      -WindowStyle Hidden -PassThru

$vigilante.Id | Out-File -FilePath "$raiz\spoc-vigilante-pid.txt" -Encoding ascii
Write-Output "vigilante lanzado, PID $($vigilante.Id), piso $piso"
