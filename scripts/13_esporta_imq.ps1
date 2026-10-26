# 13_esporta_imq.ps1 - Fase 1 del piano IMQ 2022: esporta l'Access in CSV.
#
# Legge in sola lettura data/raw/IMQ2022_opendata_web/IMQ2022_opendata_web.accdb
# col driver ODBC "Microsoft Access Driver (*.mdb, *.accdb)" (gia' installato).
# Scrive in data/processed/imq/: interviste.csv, spostamenti.csv, zone_camp.csv,
# comuni.csv, scopi.csv, mezzi.csv.
#
# Formato: UTF-8 senza BOM, separatore ";", punto decimale, ORA_* come testo HH:mm.
# Privacy: NON vengono MAI selezionati ID_INT, PHONE, MOBILE_FISSO, CONSENSO,
# FISSO_MOBILE, IN_ELENCO (regola in sviluppo/MEMORIA_PROGETTO.md).
#
# L'export e' in C# compilato al volo (Add-Type): le 95.608 righe di spostamenti
# scritte cella per cella in PowerShell puro impiegavano minuti.
#
# Uso:  powershell -ExecutionPolicy Bypass -File scripts\13_esporta_imq.ps1

$ErrorActionPreference = 'Stop'

$Root   = Split-Path -Parent $PSScriptRoot
$Db     = Join-Path $Root 'data\raw\IMQ2022_opendata_web\IMQ2022_opendata_web.accdb'
$OutDir = Join-Path $Root 'data\processed\imq'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

if (-not (Test-Path $Db)) { throw "Database IMQ non trovato: $Db" }

$Codice = @'
using System;
using System.Data;
using System.Data.Odbc;
using System.Globalization;
using System.IO;
using System.Text;

public static class ImqExport
{
    class Tab
    {
        public string Name;
        public string File;
        public string[] Cols;
        public Tab(string n, string f, string[] c) { Name = n; File = f; Cols = c; }
    }

    static string Fmt(object v)
    {
        if (v == null || v is DBNull) return "";
        if (v is DateTime)
        {
            DateTime d = (DateTime)v;
            if (d.Year < 1900) return d.ToString("HH:mm");   // 30/12/1899 = solo ora
            return d.ToString("yyyy-MM-dd");
        }
        if (v is double) return ((double)v).ToString("R", CultureInfo.InvariantCulture);
        if (v is float) return ((float)v).ToString("R", CultureInfo.InvariantCulture);
        if (v is decimal) return ((decimal)v).ToString(CultureInfo.InvariantCulture);
        return Convert.ToString(v, CultureInfo.InvariantCulture);
    }

    static string Quote(string s)
    {
        if (s.IndexOf(';') >= 0 || s.IndexOf('"') >= 0 || s.IndexOf('\n') >= 0 || s.IndexOf('\r') >= 0)
            return "\"" + s.Replace("\"", "\"\"") + "\"";
        return s;
    }

    public static void Run(string db, string outDir)
    {
        Tab[] tabs = new Tab[] {
            new Tab("interviste", "interviste.csv", new string[] {
                "LOTTO","GIORNO","COD_CAMP","MACRO_CAMP","COD_DIM","MACRO_DIM","SESSO",
                "FASCIA_ETA","TRASP","Q_USC","N_SPOST","N_AUTO","ATTIVITA","TIPO_STUD",
                "DAD","LAVORA","SETTORE_LAV","AGILE","TITOLO_STUDIO","DIMORA_ABIT",
                "RESID_ANAGR","PESO" }),
            new Tab("spostamenti", "spostamenti.csv", new string[] {
                "LOTTO","SESSO","ATTIVITA","COD_CAMP","COD_DIM","PROGR_USC","PROGR_SPOST",
                "SCOPO","COD_PAR","ORA_PAR","COD_ARR","ORA_ARR","USO_MEZZ","MEZZO1",
                "MEZZO2","MEZZO3","PAX_AUTO","NUM_LIN_URB","COD_ALTROURB","ORA_2MEZZO",
                "COD_2M","ORA_3MEZZO","COD_3M","PESO" }),
            new Tab("tab_zone_camp", "zone_camp.csv", new string[] {
                "COD2","DENOMINAZIONE","MACRO_CAMP","PROVINCIA","BACINO" }),
            new Tab("tab_comuni", "comuni.csv", new string[] {
                "COD1_ISTAT","COD1","COD2","MACRO_CAMP","DESCRIZIONE" }),
            new Tab("tab_scopi", "scopi.csv", new string[] { "Cod_Scopo", "Label" }),
            new Tab("tab_mezzi", "mezzi.csv", new string[] {
                "Cod_Mezzo","Label","cod_tipo_mezzo","label_tipo_mezzo" })
        };

        string cs = "Driver={Microsoft Access Driver (*.mdb, *.accdb)};Dbq=" + db + ";";
        UTF8Encoding enc = new UTF8Encoding(false);
        using (OdbcConnection conn = new OdbcConnection(cs))
        {
            conn.Open();
            foreach (Tab t in tabs)
            {
                using (OdbcCommand cmd = new OdbcCommand(
                           "SELECT " + string.Join(", ", t.Cols) + " FROM " + t.Name, conn))
                using (OdbcDataReader rd = cmd.ExecuteReader())
                {
                    string path = Path.Combine(outDir, t.File);
                    using (StreamWriter sw = new StreamWriter(path, false, enc))
                    {
                        sw.WriteLine(string.Join(";", t.Cols));
                        string[] vals = new string[t.Cols.Length];
                        while (rd.Read())
                        {
                            for (int i = 0; i < t.Cols.Length; i++)
                                vals[i] = Quote(Fmt(rd.GetValue(i)));
                            sw.WriteLine(string.Join(";", vals));
                        }
                    }
                }
                Console.WriteLine(t.Name + " -> " + t.File);
            }
        }
    }
}
'@

if (-not ('ImqExport' -as [type])) {
  Add-Type -TypeDefinition $Codice -ReferencedAssemblies 'System.Data'
}

[ImqExport]::Run($Db, $OutDir)
