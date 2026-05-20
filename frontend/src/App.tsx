import { Activity, BarChart3, Check, ChevronDown, Dna, FlaskConical, RefreshCw, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { Job, runTcgaCorrelation, runTcgaExpression, runTcgaSurvival, runTumorNormal, runOra, runGsea } from "./api/client";

type AppModule = "tcga" | "enrichment";
type AnalysisKey =
  | "tcga_survival"
  | "tcga_correlation"
  | "tcga_tumor_normal"
  | "tcga_expression"
  | "enrichment_ora"
  | "enrichment_gsea";

type ComboOption<T extends string = string> = {
  label: string;
  value: T;
  disabled?: boolean;
  description?: string;
};

const analysisOptions: Record<Exclude<AppModule, "jobs">, ComboOption<AnalysisKey>[]> = {
  tcga: [
    { label: "Survival analysis", value: "tcga_survival" },
    { label: "Gene correlation", value: "tcga_correlation" },
    { label: "Tumor vs normal", value: "tcga_tumor_normal" },
    { label: "Expression view", value: "tcga_expression" }
  ],
  enrichment: [
    { label: "ORA enrichment", value: "enrichment_ora" },
    { label: "GSEA enrichment", value: "enrichment_gsea" }
  ]
};

const moduleTitle: Record<AppModule, string> = {
  tcga: "TCGA PanCancer",
  enrichment: "Gene Enrichment"
};

const cancerProjects: ComboOption[] = [
  { label: "TCGA-ACC", value: "TCGA-ACC", description: "Adrenocortical carcinoma" },
  { label: "TCGA-BLCA", value: "TCGA-BLCA", description: "Bladder urothelial carcinoma" },
  { label: "TCGA-BRCA", value: "TCGA-BRCA", description: "Breast invasive carcinoma" },
  { label: "TCGA-CESC", value: "TCGA-CESC", description: "Cervical squamous cell carcinoma and endocervical adenocarcinoma" },
  { label: "TCGA-CHOL", value: "TCGA-CHOL", description: "Cholangiocarcinoma" },
  { label: "TCGA-COAD", value: "TCGA-COAD", description: "Colon adenocarcinoma" },
  { label: "TCGA-DLBC", value: "TCGA-DLBC", description: "Lymphoid neoplasm diffuse large B-cell lymphoma" },
  { label: "TCGA-ESCA", value: "TCGA-ESCA", description: "Esophageal carcinoma" },
  { label: "TCGA-GBM", value: "TCGA-GBM", description: "Glioblastoma multiforme" },
  { label: "TCGA-HNSC", value: "TCGA-HNSC", description: "Head and neck squamous cell carcinoma" },
  { label: "TCGA-KICH", value: "TCGA-KICH", description: "Kidney chromophobe" },
  { label: "TCGA-KIRC", value: "TCGA-KIRC", description: "Kidney renal clear cell carcinoma" },
  { label: "TCGA-KIRP", value: "TCGA-KIRP", description: "Kidney renal papillary cell carcinoma" },
  { label: "TCGA-LAML", value: "TCGA-LAML", description: "Acute myeloid leukemia" },
  { label: "TCGA-LGG", value: "TCGA-LGG", description: "Brain lower grade glioma" },
  { label: "TCGA-LIHC", value: "TCGA-LIHC", description: "Liver hepatocellular carcinoma" },
  { label: "TCGA-LUAD", value: "TCGA-LUAD", description: "Lung adenocarcinoma" },
  { label: "TCGA-LUSC", value: "TCGA-LUSC", description: "Lung squamous cell carcinoma" },
  { label: "TCGA-MESO", value: "TCGA-MESO", description: "Mesothelioma" },
  { label: "TCGA-OV", value: "TCGA-OV", description: "Ovarian serous cystadenocarcinoma" },
  { label: "TCGA-PAAD", value: "TCGA-PAAD", description: "Pancreatic adenocarcinoma" },
  { label: "TCGA-PCPG", value: "TCGA-PCPG", description: "Pheochromocytoma and paraganglioma" },
  { label: "TCGA-PRAD", value: "TCGA-PRAD", description: "Prostate adenocarcinoma" },
  { label: "TCGA-READ", value: "TCGA-READ", description: "Rectum adenocarcinoma" },
  { label: "TCGA-SARC", value: "TCGA-SARC", description: "Sarcoma" },
  { label: "TCGA-SKCM", value: "TCGA-SKCM", description: "Skin cutaneous melanoma" },
  { label: "TCGA-STAD", value: "TCGA-STAD", description: "Stomach adenocarcinoma" },
  { label: "TCGA-TGCT", value: "TCGA-TGCT", description: "Testicular germ cell tumors" },
  { label: "TCGA-THCA", value: "TCGA-THCA", description: "Thyroid carcinoma" },
  { label: "TCGA-THYM", value: "TCGA-THYM", description: "Thymoma" },
  { label: "TCGA-UCEC", value: "TCGA-UCEC", description: "Uterine corpus endometrial carcinoma" },
  { label: "TCGA-UCS", value: "TCGA-UCS", description: "Uterine carcinosarcoma" },
  { label: "TCGA-UVM", value: "TCGA-UVM", description: "Uveal melanoma" }
];

const survivalMetrics: ComboOption[] = [
  { label: "OS", value: "OS" },
  { label: "DSS", value: "DSS" },
  { label: "PFI", value: "PFI" },
  { label: "DFI", value: "DFI" }
];

const axisUnits: ComboOption[] = [
  { label: "Days", value: "days", description: "天" },
  { label: "Months", value: "months", description: "月" }
];

const groupingMethods: ComboOption<"median" | "percentile" | "optimal">[] = [
  { label: "Median split", value: "median" },
  { label: "Manual percentile", value: "percentile" },
  { label: "Optimal threshold", value: "optimal" }
];

const correlationMethods: ComboOption[] = [
  { label: "Pearson", value: "pearson" },
  { label: "Spearman", value: "spearman" }
];

const expressionSortOptions: ComboOption[] = [
  { label: "Alphabetical", value: "alphabetical" },
  { label: "Expression high to low", value: "expression_desc" }
];

const oraCollections: ComboOption[] = [
  { label: "Select all", value: "ALL" },
  { label: "Hallmark", value: "hallmark" },
  { label: "KEGG pathways", value: "kegg_pathways" },
  { label: "Reactome pathways", value: "reactome_pathways" },
  { label: "WikiPathways", value: "wikipathways" },
  { label: "BioCarta pathways", value: "biocarta_pathways" },
  { label: "PID pathways", value: "pid_pathways" },
  { label: "GO biological process", value: "go_biological_process" },
  { label: "GO cellular component", value: "go_cellular_component" },
  { label: "GO molecular function", value: "go_molecular_function" },
  { label: "Chemical and genetic perturbations", value: "chemical_and_genetic_perturbations" },
  { label: "Immunologic signatures", value: "immunesigdb" },
  { label: "Oncogenic signatures", value: "oncogenic_signatures" },
  { label: "Cell type signatures", value: "cell_type_signatures" },
  { label: "Positional", value: "positional" },
  { label: "Cancer modules", value: "cancer_modules" },
  { label: "Cancer cell atlas", value: "cancer_cell_atlas" },
  { label: "Cancer gene neighborhoods", value: "cancer_gene_neighborhoods" },
  { label: "TF targets legacy", value: "tf_targets_legacy" },
  { label: "TF targets GTRF", value: "tf_targets_gtrf" },
  { label: "miRNA targets legacy", value: "mirna_targets_legacy" },
  { label: "miRNA targets miRDB", value: "mirna_targets_mirdb" },
  { label: "Human phenotype ontology", value: "human_phenotype_ontology" },
  { label: "KEGG Medicus pathways", value: "kegg_medicus_pathways" },
  { label: "Vaccine response", value: "vaccine_response" }
];

function splitGenes(value: string): string[] {
  return value
    .split(/[\s,;]+/)
    .map((gene) => gene.trim())
    .filter(Boolean);
}

function parseRankings(value: string): { gene: string; score: number }[] {
  return value
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => line.split(/[\s,]+/))
    .filter((parts) => parts.length >= 2 && Number.isFinite(Number(parts[1])))
    .map((parts) => ({ gene: parts[0], score: Number(parts[1]) }));
}

function runningMessage(analysis: AnalysisKey): string {
  switch (analysis) {
    case "tcga_survival":
      return "Running survival analysis. The first run may take tens of seconds while reading the TCGA matrix.";
    case "tcga_correlation":
      return "Running gene correlation analysis.";
    case "tcga_tumor_normal":
      return "Running tumor vs normal comparison.";
    case "tcga_expression":
      return "Running expression visualization.";
    case "enrichment_ora":
      return "Running ORA enrichment.";
    case "enrichment_gsea":
      return "Running GSEA enrichment.";
  }
}

function ResultTable({ job }: { job: Job | null }) {
  const records = job?.result?.records;
  if (!Array.isArray(records) || records.length === 0) {
    return <div className="empty">No table result yet.</div>;
  }
  const columns = Object.keys(records[0] as Record<string, unknown>);
  return (
    <div className="tableWrap">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {records.map((row, index) => (
            <tr key={index}>
              {columns.map((column) => (
                <td key={column}>{String((row as Record<string, unknown>)[column])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ComboBox<T extends string>({
  label,
  options,
  value,
  onChange
}: {
  label: string;
  options: ComboOption<T>[];
  value: T;
  onChange: (value: T) => void;
}) {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const selected = options.find((option) => option.value === value);
  const visibleOptions = useMemo(() => {
    const text = query.trim().toLowerCase();
    const enabled = options.filter((option) => !option.disabled);
    if (!text || !isOpen) {
      return enabled;
    }
    return enabled.filter((option) =>
      [option.label, option.value, option.description ?? "", option.value.replace("TCGA-", "")]
        .join(" ")
        .toLowerCase()
        .includes(text)
    );
  }, [isOpen, options, query]);

  function pick(option: ComboOption<T>) {
    onChange(option.value);
    setQuery("");
    setIsOpen(false);
  }

  return (
    <label className="comboField" onBlur={(event) => {
      if (!event.currentTarget.contains(event.relatedTarget)) {
        setIsOpen(false);
        setQuery("");
      }
    }}>
      <span>{label}</span>
      <div className="comboControl">
        <input
          value={isOpen ? query : selected?.label ?? value}
          onChange={(event) => {
            setQuery(event.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
        />
        <button
          className="comboButton"
          title={`Show ${label} options`}
          type="button"
          onClick={() => {
            setQuery("");
            setIsOpen((open) => !open);
          }}
        >
          <ChevronDown size={16} />
        </button>
      </div>
      {isOpen && (
        <div className="comboMenu" tabIndex={-1}>
          {visibleOptions.map((option) => (
            <button key={option.value} type="button" className="comboOption" onMouseDown={(event) => event.preventDefault()} onClick={() => pick(option)}>
              <span>{option.label}</span>
              {option.description && <small>{option.description}</small>}
            </button>
          ))}
          {visibleOptions.length === 0 && <div className="comboEmpty">No matches</div>}
        </div>
      )}
    </label>
  );
}

function MultiSelect({
  label,
  options,
  values,
  onChange
}: {
  label: string;
  options: ComboOption[];
  values: string[];
  onChange: (values: string[]) => void;
}) {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const selected = new Set(values);
  const selectedOptions = values.includes("ALL")
    ? [{ label: "All collections", value: "ALL" }]
    : options.filter((option) => values.includes(option.value));
  const visibleOptions = useMemo(() => {
    const text = query.trim().toLowerCase();
    const enabled = options.filter((option) => !option.disabled);
    if (!text || !isOpen) {
      return enabled;
    }
    return enabled.filter((option) =>
      [option.label, option.value, option.description ?? ""].join(" ").toLowerCase().includes(text)
    );
  }, [isOpen, options, query]);

  function toggle(option: ComboOption) {
    if (option.value === "ALL") {
      onChange(values.includes("ALL") ? [] : ["ALL"]);
      return;
    }
    const next = selected.has(option.value)
      ? values.filter((value) => value !== option.value && value !== "ALL")
      : [...values.filter((value) => value !== "ALL"), option.value];
    onChange(next);
  }

  return (
    <div className="comboField" onBlur={(event) => {
      if (!event.currentTarget.contains(event.relatedTarget)) {
        setIsOpen(false);
        setQuery("");
      }
    }}>
      <span>{label}</span>
      <div className="multiSelectControl" onClick={() => setIsOpen(true)}>
        {selectedOptions.map((option) => (
          <button
            key={option.value}
            type="button"
            className="selectedPill"
            onClick={(event) => {
              event.stopPropagation();
              toggle(option);
            }}
          >
            <span>{option.label}</span>
            <span aria-hidden="true">x</span>
          </button>
        ))}
        <input
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setIsOpen(true);
          }}
          placeholder={selectedOptions.length === 0 ? "Choose options" : ""}
          onFocus={() => setIsOpen(true)}
        />
        <button
          className="multiSelectButton"
          title={`Show ${label} options`}
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            setQuery("");
            setIsOpen((open) => !open);
          }}
        >
          <ChevronDown size={16} />
        </button>
      </div>
      {isOpen && (
        <div className="comboMenu" tabIndex={-1}>
          {visibleOptions.map((option) => (
            <button
              key={option.value}
              type="button"
              className="comboOption multiOption"
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => toggle(option)}
            >
              <span className="checkCell">{selected.has(option.value) && <Check size={15} />}</span>
              <span>{option.label}</span>
              {option.description && <small>{option.description}</small>}
            </button>
          ))}
          {visibleOptions.length === 0 && <div className="comboEmpty">No matches</div>}
        </div>
      )}
    </div>
  );
}

function Summary({ job }: { job: Job | null }) {
  const summary = job?.result?.summary;
  if (!summary || typeof summary !== "object") {
    return null;
  }
  return (
    <dl className="summaryGrid">
      {Object.entries(summary as Record<string, unknown>)
        .filter(([key]) => key !== "plot_url")
        .map(([key, value]) => (
          <div key={key}>
            <dt>{key}</dt>
            <dd>{typeof value === "number" ? value.toPrecision(4) : Array.isArray(value) ? value.join(", ") : String(value)}</dd>
          </div>
        ))}
    </dl>
  );
}

function ResultPlot({ job, onZoom }: { job: Job | null; onZoom: (url: string) => void }) {
  const plotUrl = job?.result?.plot_url;
  if (typeof plotUrl !== "string") {
    return null;
  }
  return (
    <div className="plotFrame">
      <button className="plotZoomButton" title="Zoom image" type="button" onClick={() => onZoom(plotUrl)}>
        <Search size={17} />
      </button>
      <img src={plotUrl} alt="Kaplan-Meier survival plot" />
    </div>
  );
}

function SurvivalAnalysisPanel({
  project,
  setProject,
  genes,
  setGenes,
  groupingMethod,
  setGroupingMethod,
  highPercentile,
  setHighPercentile,
  survivalMetric,
  setSurvivalMetric,
  axisUnit,
  setAxisUnit,
  onRun,
  isRunning
}: {
  project: string;
  setProject: (value: string) => void;
  genes: string;
  setGenes: (value: string) => void;
  groupingMethod: "median" | "percentile" | "optimal";
  setGroupingMethod: (value: "median" | "percentile" | "optimal") => void;
  highPercentile: number;
  setHighPercentile: (value: number) => void;
  survivalMetric: string;
  setSurvivalMetric: (value: string) => void;
  axisUnit: string;
  setAxisUnit: (value: string) => void;
  onRun: () => void;
  isRunning: boolean;
}) {
  return (
    <form className="analysisForm" onSubmit={(event) => event.preventDefault()}>
      <div className="formGrid">
        <ComboBox label="Cancer project" options={cancerProjects} value={project} onChange={setProject} />
        <ComboBox label="Survival endpoint" options={survivalMetrics} value={survivalMetric} onChange={setSurvivalMetric} />
        <ComboBox label="Time unit" options={axisUnits} value={axisUnit} onChange={setAxisUnit} />
        <ComboBox label="Grouping method" options={groupingMethods} value={groupingMethod} onChange={setGroupingMethod} />
        {groupingMethod === "percentile" && (
          <label>
            High group percentile
            <input
              min={1}
              max={99}
              type="number"
              value={highPercentile}
              onChange={(event) => setHighPercentile(Number(event.target.value))}
            />
          </label>
        )}
      </div>
      <label>
        Signature genes
        <textarea value={genes} onChange={(event) => setGenes(event.target.value)} />
      </label>
      <div className="buttonRow">
        <button disabled={isRunning} onClick={onRun}>
          {isRunning ? "Running..." : "Run survival analysis"}
        </button>
      </div>
    </form>
  );
}

function TumorNormalPanel({
  project,
  setProject,
  gene,
  setGene,
  showPoints,
  setShowPoints,
  onRun,
  isRunning
}: {
  project: string;
  setProject: (value: string) => void;
  gene: string;
  setGene: (value: string) => void;
  showPoints: boolean;
  setShowPoints: (value: boolean) => void;
  onRun: () => void;
  isRunning: boolean;
}) {
  return (
    <form className="analysisForm" onSubmit={(event) => event.preventDefault()}>
      <div className="compactFormGrid">
        <ComboBox label="Cancer project" options={cancerProjects} value={project} onChange={setProject} />
        <label>
          Gene
          <textarea
            value={gene}
            onChange={(event) => setGene(event.target.value)}
            placeholder={"e.g. TP53\nSeparators: space, comma, or newline"}
          />
        </label>
      </div>
      <label className="checkboxLabel">
        <input
          type="checkbox"
          checked={showPoints}
          onChange={(event) => setShowPoints(event.target.checked)}
        />
        Show data points
      </label>
      <div className="buttonRow">
        <button disabled={isRunning} onClick={onRun}>
          {isRunning ? "Running..." : "Run tumor vs normal"}
        </button>
      </div>
    </form>
  );
}

function CorrelationAnalysisPanel({
  project,
  setProject,
  genes,
  setGenes,
  targetGenes,
  setTargetGenes,
  method,
  setMethod,
  onRun,
  isRunning
}: {
  project: string;
  setProject: (value: string) => void;
  genes: string;
  setGenes: (value: string) => void;
  targetGenes: string;
  setTargetGenes: (value: string) => void;
  method: string;
  setMethod: (value: string) => void;
  onRun: () => void;
  isRunning: boolean;
}) {
  return (
    <form className="analysisForm" onSubmit={(event) => event.preventDefault()}>
      <div className="formGrid">
        <ComboBox label="Cancer project" options={cancerProjects} value={project} onChange={setProject} />
        <ComboBox label="Correlation method" options={correlationMethods} value={method} onChange={setMethod} />
      </div>
      <label>
        Signature genes (x)
        <textarea
          value={genes}
          onChange={(event) => setGenes(event.target.value)}
          placeholder="e.g. CD3D, CD3E"
        />
      </label>
      <label>
        Signature genes (y)
        <textarea
          value={targetGenes}
          onChange={(event) => setTargetGenes(event.target.value)}
          placeholder="e.g. PDCD1, CD274, CTLA4"
        />
      </label>
      <div className="buttonRow">
        <button disabled={isRunning} onClick={onRun}>
          {isRunning ? "Running..." : "Run correlation analysis"}
        </button>
      </div>
    </form>
  );
}

function ExpressionPanel({
  genes,
  setGenes,
  sortBy,
  setSortBy,
  showPoints,
  setShowPoints,
  onRun,
  isRunning
}: {
  genes: string;
  setGenes: (value: string) => void;
  sortBy: string;
  setSortBy: (value: string) => void;
  showPoints: boolean;
  setShowPoints: (value: boolean) => void;
  onRun: () => void;
  isRunning: boolean;
}) {
  return (
    <form className="analysisForm" onSubmit={(event) => event.preventDefault()}>
      <div className="compactFormGrid">
        <ComboBox label="Sort projects" options={expressionSortOptions} value={sortBy} onChange={setSortBy} />
        <label>
          Genes
          <textarea
            value={genes}
            onChange={(event) => setGenes(event.target.value)}
            placeholder={"e.g. TP53 MDM2 CDKN1A\nSeparators: space, comma, or newline"}
          />
        </label>
      </div>
      <label className="checkboxLabel">
        <input
          type="checkbox"
          checked={showPoints}
          onChange={(event) => setShowPoints(event.target.checked)}
        />
        Show data points
      </label>
      <div className="buttonRow">
        <button disabled={isRunning} onClick={onRun}>
          {isRunning ? "Running..." : "Run expression view"}
        </button>
      </div>
    </form>
  );
}

function OraPanel({
  genes,
  setGenes,
  upGenes,
  setUpGenes,
  downGenes,
  setDownGenes,
  backgroundGenes,
  setBackgroundGenes,
  collections,
  setCollections,
  minOverlap,
  setMinOverlap,
  topN,
  setTopN,
  fdrThreshold,
  setFdrThreshold,
  onRun,
  isRunning
}: {
  genes: string;
  setGenes: (value: string) => void;
  upGenes: string;
  setUpGenes: (value: string) => void;
  downGenes: string;
  setDownGenes: (value: string) => void;
  backgroundGenes: string;
  setBackgroundGenes: (value: string) => void;
  collections: string[];
  setCollections: (value: string[]) => void;
  minOverlap: number;
  setMinOverlap: (value: number) => void;
  topN: number;
  setTopN: (value: number) => void;
  fdrThreshold: number;
  setFdrThreshold: (value: number) => void;
  onRun: () => void;
  isRunning: boolean;
}) {
  return (
    <form className="analysisForm" onSubmit={(event) => event.preventDefault()}>
      <MultiSelect label="Gene set collection" options={oraCollections} values={collections} onChange={setCollections} />
      <div className="formGrid">
        <label>
          Min overlap
          <input
            min={1}
            max={100}
            type="number"
            value={minOverlap}
            onChange={(event) => setMinOverlap(Number(event.target.value))}
          />
        </label>
        <label>
          Max terms
          <input
            min={1}
            max={100}
            type="number"
            value={topN}
            onChange={(event) => setTopN(Number(event.target.value))}
          />
        </label>
        <label>
          FDR threshold
          <input
            min={0}
            max={1}
            step={0.001}
            type="number"
            value={fdrThreshold}
            onChange={(event) => setFdrThreshold(Number(event.target.value))}
          />
        </label>
      </div>
      <p className="formHint">
        Use Query genes for one ORA run, or fill Up genes and Down genes to run separate enrichment groups.
        Background genes are optional.
      </p>
      <label>
        Query genes
        <textarea
          value={genes}
          onChange={(event) => setGenes(event.target.value)}
          placeholder={"e.g. TP53 MDM2 CDKN1A\nor TP53, MDM2, CDKN1A"}
        />
      </label>
      <div className="formGrid">
        <label>
          Up genes
          <textarea value={upGenes} onChange={(event) => setUpGenes(event.target.value)} />
        </label>
        <label>
          Down genes
          <textarea value={downGenes} onChange={(event) => setDownGenes(event.target.value)} />
        </label>
      </div>
      <label>
        Background genes
        <textarea
          value={backgroundGenes}
          onChange={(event) => setBackgroundGenes(event.target.value)}
          placeholder="Optional. Leave empty to use all genes in selected collections."
        />
      </label>
      <div className="buttonRow">
        <button disabled={isRunning} onClick={onRun}>
          {isRunning ? "Running..." : "Run ORA"}
        </button>
      </div>
    </form>
  );
}

function GseaPanel({
  rankings,
  setRankings,
  collections,
  setCollections,
  minOverlap,
  setMinOverlap,
  topN,
  setTopN,
  fdrThreshold,
  setFdrThreshold,
  onRun,
  isRunning
}: {
  rankings: string;
  setRankings: (value: string) => void;
  collections: string[];
  setCollections: (value: string[]) => void;
  minOverlap: number;
  setMinOverlap: (value: number) => void;
  topN: number;
  setTopN: (value: number) => void;
  fdrThreshold: number;
  setFdrThreshold: (value: number) => void;
  onRun: () => void;
  isRunning: boolean;
}) {
  return (
    <form className="analysisForm" onSubmit={(event) => event.preventDefault()}>
      <MultiSelect label="Gene set collection" options={oraCollections} values={collections} onChange={setCollections} />
      <div className="formGrid">
        <label>
          Min overlap
          <input min={1} max={100} type="number" value={minOverlap} onChange={(event) => setMinOverlap(Number(event.target.value))} />
        </label>
        <label>
          Max terms
          <input min={1} max={100} type="number" value={topN} onChange={(event) => setTopN(Number(event.target.value))} />
        </label>
        <label>
          FDR threshold
          <input
            min={0}
            max={1}
            step={0.001}
            type="number"
            value={fdrThreshold}
            onChange={(event) => setFdrThreshold(Number(event.target.value))}
          />
        </label>
      </div>
      <label>
        Ranked genes
        <textarea
          value={rankings}
          onChange={(event) => setRankings(event.target.value)}
          placeholder={"One gene and score per line:\nTP53 2.4\nMDM2 1.1\nEGFR -1.8"}
        />
      </label>
      <div className="buttonRow">
        <button disabled={isRunning} onClick={onRun}>
          {isRunning ? "Running..." : "Run GSEA"}
        </button>
      </div>
    </form>
  );
}

export function App() {
  const [active, setActive] = useState<AppModule>("tcga");
  const [analysis, setAnalysis] = useState<AnalysisKey>("tcga_survival");
  const [project, setProject] = useState("TCGA-LUAD");
  const [genes, setGenes] = useState("TP53");
  const [tumorNormalGene, setTumorNormalGene] = useState("TP53");
  const [expressionGenes, setExpressionGenes] = useState("TP53");
  const [expressionSortBy, setExpressionSortBy] = useState("alphabetical");
  const [groupingMethod, setGroupingMethod] = useState<"median" | "percentile" | "optimal">("median");
  const [highPercentile, setHighPercentile] = useState(50);
  const [survivalMetric, setSurvivalMetric] = useState("OS");
  const [axisUnit, setAxisUnit] = useState("days");
  const [targetGenes, setTargetGenes] = useState("PDCD1");
  const [correlationMethod, setCorrelationMethod] = useState("pearson");
  const [showPoints, setShowPoints] = useState(true);
  const [oraGenes, setOraGenes] = useState("TP53, MDM2, CDKN1A");
  const [oraUpGenes, setOraUpGenes] = useState("");
  const [oraDownGenes, setOraDownGenes] = useState("");
  const [oraBackgroundGenes, setOraBackgroundGenes] = useState("");
  const [oraCollectionsSelected, setOraCollectionsSelected] = useState<string[]>(["hallmark", "kegg_pathways"]);
  const [oraMinOverlap, setOraMinOverlap] = useState(2);
  const [oraTopN, setOraTopN] = useState(10);
  const [oraFdrThreshold, setOraFdrThreshold] = useState(0.05);
  const [gseaRankings, setGseaRankings] = useState("TP53 2.4\nMDM2 1.1\nCDKN1A 0.9\nEGFR -1.8\nMYC -2.1");
  const [gseaCollectionsSelected, setGseaCollectionsSelected] = useState<string[]>(["hallmark", "kegg_pathways"]);
  const [gseaMinOverlap, setGseaMinOverlap] = useState(2);
  const [gseaTopN, setGseaTopN] = useState(10);
  const [gseaFdrThreshold, setGseaFdrThreshold] = useState(1);
  const [latestJob, setLatestJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [zoomImageUrl, setZoomImageUrl] = useState<string | null>(null);

  async function submit(action: () => Promise<Job>) {
    setError(null);
    setIsRunning(true);
    try {
      const job = await action();
      if (job.status === "failed") {
        setError(job.error ?? "Analysis failed");
      }
      setLatestJob(job);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setIsRunning(false);
    }
  }

  function changeModule(next: AppModule) {
    setActive(next);
    if (next === "tcga") {
      setAnalysis("tcga_survival");
    }
    if (next === "enrichment") {
      setAnalysis("enrichment_ora");
    }
  }

  function runSurvival() {
    submit(() =>
      runTcgaSurvival({
        project,
        genes: splitGenes(genes),
        grouping_method: groupingMethod,
        high_percentile: groupingMethod === "percentile" ? highPercentile : undefined,
        survival_metric: survivalMetric,
        axis_unit: axisUnit
      })
    );
  }

  function runCorrelation() {
    submit(() =>
      runTcgaCorrelation({
        project,
        genes: splitGenes(genes),
        target_genes: splitGenes(targetGenes),
        method: correlationMethod
      })
    );
  }

  function runOraAnalysis() {
    submit(() =>
      runOra({
        genes: splitGenes(oraGenes),
        up_genes: splitGenes(oraUpGenes),
        down_genes: splitGenes(oraDownGenes),
        background_genes: splitGenes(oraBackgroundGenes),
        collections: oraCollectionsSelected,
        min_overlap: oraMinOverlap,
        top_n: oraTopN,
        fdr_threshold: oraFdrThreshold
      })
    );
  }

  function runGseaAnalysis() {
    submit(() =>
      runGsea({
        rankings: parseRankings(gseaRankings),
        collections: gseaCollectionsSelected,
        min_overlap: gseaMinOverlap,
        top_n: gseaTopN,
        fdr_threshold: gseaFdrThreshold
      })
    );
  }

  function runTumorNormalAnalysis() {
    submit(() =>
      runTumorNormal({
        project,
        genes: splitGenes(tumorNormalGene),
        show_points: showPoints
      })
    );
  }

  function runExpressionAnalysis() {
    submit(() =>
      runTcgaExpression({
        project: "ALL",
        genes: splitGenes(expressionGenes),
        sort_by: expressionSortBy,
        show_points: showPoints
      })
    );
  }

  return (
    <main className="appShell">
      <aside className="sidebar">
        <div className="brand">
          <Dna size={24} />
          <span>BioWeb</span>
        </div>
        <button className={active === "tcga" ? "active" : ""} onClick={() => changeModule("tcga")}>
          <Activity size={18} /> TCGA
        </button>
        <button className={active === "enrichment" ? "active" : ""} onClick={() => changeModule("enrichment")}>
          <FlaskConical size={18} /> Enrichment
        </button>
      </aside>

      <section className="workspace">
        <header>
          <div>
            <h1>{moduleTitle[active]}</h1>
            <p className="subtitle">Choose one analysis and run it independently.</p>
          </div>
          <button className="iconButton" title="Clear result" onClick={() => setLatestJob(null)}>
            <RefreshCw size={18} />
          </button>
        </header>

        {error && <div className="error">{error}</div>}

        <div className="analysisLayout">
          <div className="grid">
            <section className="panel analysisPanel">
              <div className="analysisPicker">
                <ComboBox
                  label="Analysis"
                  options={analysisOptions[active]}
                  value={analysis}
                  onChange={(value) => {
                    const option = analysisOptions[active].find((item) => item.value === value);
                    if (!option?.disabled) {
                      setAnalysis(value);
                    }
                  }}
                />
              </div>
              <h2>
                {analysis === "tcga_survival"
                  ? "Survival Analysis"
                  : analysis === "tcga_correlation"
                    ? "Gene Correlation"
                    : analysis === "tcga_tumor_normal"
                      ? "Tumor vs Normal"
                      : analysis === "tcga_expression"
                        ? "Expression View"
                      : analysis === "enrichment_ora"
                        ? "ORA Enrichment"
                        : analysis === "enrichment_gsea"
                          ? "GSEA Enrichment"
                        : "Analysis"}
              </h2>
              {analysis === "tcga_survival" ? (
                <SurvivalAnalysisPanel
                  axisUnit={axisUnit}
                  genes={genes}
                  groupingMethod={groupingMethod}
                  highPercentile={highPercentile}
                  project={project}
                  setAxisUnit={setAxisUnit}
                  setGenes={setGenes}
                  setGroupingMethod={setGroupingMethod}
                  setHighPercentile={setHighPercentile}
                  setProject={setProject}
                  setSurvivalMetric={setSurvivalMetric}
                  survivalMetric={survivalMetric}
                  isRunning={isRunning}
                  onRun={runSurvival}
                />
              ) : analysis === "tcga_tumor_normal" ? (
                <TumorNormalPanel
                  gene={tumorNormalGene}
                  isRunning={isRunning}
                  project={project}
                  setGene={setTumorNormalGene}
                  setProject={setProject}
                  showPoints={showPoints}
                  setShowPoints={setShowPoints}
                  onRun={runTumorNormalAnalysis}
                />
              ) : analysis === "tcga_correlation" ? (
                <CorrelationAnalysisPanel
                  project={project}
                  setProject={setProject}
                  genes={genes}
                  setGenes={setGenes}
                  targetGenes={targetGenes}
                  setTargetGenes={setTargetGenes}
                  method={correlationMethod}
                  setMethod={setCorrelationMethod}
                  isRunning={isRunning}
                  onRun={runCorrelation}
                />
              ) : analysis === "tcga_expression" ? (
                <ExpressionPanel
                  genes={expressionGenes}
                  isRunning={isRunning}
                  setGenes={setExpressionGenes}
                  sortBy={expressionSortBy}
                  setSortBy={setExpressionSortBy}
                  showPoints={showPoints}
                  setShowPoints={setShowPoints}
                  onRun={runExpressionAnalysis}
                />
              ) : analysis === "enrichment_ora" ? (
                <OraPanel
                  genes={oraGenes}
                  setGenes={setOraGenes}
                  upGenes={oraUpGenes}
                  setUpGenes={setOraUpGenes}
                  downGenes={oraDownGenes}
                  setDownGenes={setOraDownGenes}
                  backgroundGenes={oraBackgroundGenes}
                  setBackgroundGenes={setOraBackgroundGenes}
                  collections={oraCollectionsSelected}
                  setCollections={setOraCollectionsSelected}
                  minOverlap={oraMinOverlap}
                  setMinOverlap={setOraMinOverlap}
                  topN={oraTopN}
                  setTopN={setOraTopN}
                  fdrThreshold={oraFdrThreshold}
                  setFdrThreshold={setOraFdrThreshold}
                  isRunning={isRunning}
                  onRun={runOraAnalysis}
                />
              ) : analysis === "enrichment_gsea" ? (
                <GseaPanel
                  rankings={gseaRankings}
                  setRankings={setGseaRankings}
                  collections={gseaCollectionsSelected}
                  setCollections={setGseaCollectionsSelected}
                  minOverlap={gseaMinOverlap}
                  setMinOverlap={setGseaMinOverlap}
                  topN={gseaTopN}
                  setTopN={setGseaTopN}
                  fdrThreshold={gseaFdrThreshold}
                  setFdrThreshold={setGseaFdrThreshold}
                  isRunning={isRunning}
                  onRun={runGseaAnalysis}
                />
              ) : (
                <div className="empty">This analysis has its own panel reserved and will be implemented next.</div>
              )}
            </section>
            <section className="panel resultPanel">
              <h2>Result</h2>
              {isRunning && (
                <div className="runningNotice">
                  <span className="spinner" aria-hidden="true" />
                  <span className="runningText">{runningMessage(analysis)}</span>
                </div>
              )}
              <Summary job={latestJob} />
              <ResultPlot job={latestJob} onZoom={setZoomImageUrl} />
              <ResultTable job={latestJob} />
            </section>
          </div>
        </div>
      </section>
      {zoomImageUrl && (
        <div className="imageModal" role="dialog" aria-modal="true" onClick={() => setZoomImageUrl(null)}>
          <button className="imageModalClose" type="button" onClick={() => setZoomImageUrl(null)}>
            Close
          </button>
          <img src={zoomImageUrl} alt="Expanded result plot" onClick={(event) => event.stopPropagation()} />
        </div>
      )}
    </main>
  );
}
