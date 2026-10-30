// Usage: node frontend/scripts/facts.mjs <file>..., from the repository's root: prints, as JSON, the facts of each
// TypeScript or Svelte file, as dev/src/chatddx_dev/stamp/facts.py:Facts holds them: the names it defines and the
// lines they span, its comments, lines from 1 and columns from 0, and its surface's entries, rendered.
// Duplication: dev/src/chatddx_dev/stamp/frontend.py:LEGEND tells how to read the entries rendered here.
import { readFileSync } from "node:fs";
import { parse } from "svelte/compiler";
import ts from "typescript";

/** @typedef {{ name: string, line: number, end: number, column: number }} Named */
/** @typedef {{ line: number, column: number, text: string, alone: boolean }} Comment */
/** @typedef {{ name: string, heading: string, lines: string[] }} Entry */
/** @typedef {{ path: string, names: Named[], comments: Comment[], claims: never[], surface: Entry[] }} Facts */

/**
 * @param {string} source
 * @param {number} offset
 * @returns {{ line: number, column: number }}
 */
function at(source, offset) {
  const before = source.slice(0, offset);
  const begun = before.lastIndexOf("\n") + 1;
  return { line: before.split("\n").length, column: offset - begun };
}

/**
 * @param {string} source
 * @param {number} start
 * @param {number} end
 * @returns {Comment}
 */
function comment(source, start, end) {
  const { line, column } = at(source, start);
  const alone = source.slice(start - column, start).trim() === "";
  return { line, column, text: source.slice(start, end).trimEnd(), alone };
}

/**
 * @param {ts.Node} node
 * @returns {string | undefined}
 */
function named(node) {
  const name = /** @type {{ name?: ts.Node }} */ (node).name;
  return name && (ts.isIdentifier(name) || ts.isPrivateIdentifier(name)) ? name.text : undefined;
}

/**
 * @param {ts.BindingName} name
 * @returns {string[]}
 */
function bound(name) {
  if (ts.isIdentifier(name)) return [name.text];
  return name.elements.flatMap((e) => (ts.isOmittedExpression(e) ? [] : bound(e.name)));
}

// Policy: the names are what a module declares at its top, and a class's members, as Python's index anchors to.
/**
 * @param {string} source
 * @param {ts.SourceFile} file
 * @returns {Named[]}
 */
function names(source, file) {
  /** @type {Named[]} */
  const found = [];
  /**
   * @param {string} name
   * @param {ts.Node} node
   */
  const add = (name, node) => {
    const { line, column } = at(source, node.getStart(file));
    found.push({ name, line, end: at(source, node.getEnd()).line, column });
  };
  for (const statement of file.statements) {
    if (ts.isVariableStatement(statement)) {
      for (const d of statement.declarationList.declarations) {
        for (const name of bound(d.name)) add(name, statement);
      }
      continue;
    }
    const name = named(statement);
    if (name === undefined) continue;
    add(name, statement);
    if (ts.isClassDeclaration(statement)) {
      for (const member of statement.members) {
        const held = named(member);
        if (held !== undefined) add(`${name}.${held}`, member);
      }
    }
  }
  return found;
}

/**
 * @param {string} source
 * @param {ts.SourceFile} file
 * @returns {Comment[]}
 */
function comments(source, file) {
  /** @type {Map<number, Comment>} */
  const found = new Map();
  /** @param {ts.CommentRange[] | undefined} ranges */
  const add = (ranges) => {
    for (const r of ranges ?? []) found.set(r.pos, comment(source, r.pos, r.end));
  };
  /** @param {ts.Node} node */
  const visit = (node) => {
    add(ts.getLeadingCommentRanges(source, node.getFullStart()));
    add(ts.getTrailingCommentRanges(source, node.getEnd()));
    ts.forEachChild(node, visit);
  };
  visit(file);
  add(ts.getLeadingCommentRanges(source, file.endOfFileToken.getFullStart()));
  return [...found.values()];
}

/**
 * @param {string} path
 * @param {string} source
 * @returns {{ names: Named[], comments: Comment[], file: ts.SourceFile }}
 */
function typescript(path, source) {
  const file = ts.createSourceFile(path, source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  return { names: names(source, file), comments: comments(source, file), file };
}

// Duplication: dev/src/chatddx_dev/stamp/page.py:_code quotes code likewise.
/** @param {string} text */
function code(text) {
  if (!text.includes("`")) return `\`${text}\``;
  const fence = "`".repeat(Math.max(...(text.match(/`+/g) ?? []).map((run) => run.length)) + 1);
  return `${fence} ${text} ${fence}`;
}

/**
 * @param {ts.SourceFile} file
 * @param {ts.Node} node
 */
function flat(file, node) {
  return node.getText(file).replace(/\s+/g, " ").trim();
}

// Duplication: dev/src/chatddx_dev/stamp/page.py:_head cuts a value likewise.
/**
 * @param {ts.SourceFile} file
 * @param {ts.Expression} value
 */
function head(file, value) {
  const text = flat(file, value);
  if (!text.includes("\n") && text.length <= 60 && value.getText(file) === text) return text;
  if (ts.isCallExpression(value)) return `${flat(file, value.expression)}(…)`;
  if (ts.isArrayLiteralExpression(value)) return "[…]";
  if (ts.isObjectLiteralExpression(value)) return "{…}";
  return "…";
}

/** @param {ts.Node} node */
function documented(node) {
  return ts
    .getJSDocCommentsAndTags(node)
    .filter(ts.isJSDoc)
    .flatMap((d) => (ts.getTextOfJSDocComment(d.comment) ?? "").split("\n"))
    .filter((line, i, all) => line.trim() || (i > 0 && i < all.length - 1));
}

/** @param {ts.Node} node */
function exported(node) {
  return ts.canHaveModifiers(node) && (ts.getModifiers(node) ?? []).some((m) => m.kind === ts.SyntaxKind.ExportKeyword);
}

/** @param {ts.Node} node */
function hidden(node) {
  const kinds = [ts.SyntaxKind.PrivateKeyword, ts.SyntaxKind.ProtectedKeyword];
  const name = /** @type {{ name?: ts.Node }} */ (node).name;
  return (
    (name !== undefined && ts.isPrivateIdentifier(name)) ||
    (ts.canHaveModifiers(node) && (ts.getModifiers(node) ?? []).some((m) => kinds.includes(m.kind)))
  );
}

/**
 * @param {ts.SourceFile} file
 * @param {ts.ParameterDeclaration} p
 */
function parameter(file, p) {
  let written = (p.dotDotDotToken ? "..." : "") + flat(file, p.name) + (p.questionToken ? "?" : "");
  if (p.type) written += `: ${flat(file, p.type)}`;
  if (p.initializer) written += ` = ${head(file, p.initializer)}`;
  return `* ${code(written)}`;
}

/**
 * @param {ts.SourceFile} file
 * @param {ts.NodeArray<ts.TypeParameterDeclaration> | undefined} params
 */
function typed(file, params) {
  return params?.length ? [code(`<${params.map((t) => flat(file, t)).join(", ")}>`)] : [];
}

/**
 * @param {string} path
 * @param {string} name
 * @param {string[]} marks
 * @param {string[]} doc
 * @param {string[]} body
 * @returns {Entry}
 */
function entry(path, name, marks, doc, body) {
  const lines = [code(`${path}:${name}`)];
  if (doc.length) lines.push("", ...doc);
  if (body.length) lines.push("", ...body);
  return { name, heading: [code(name), ...marks].join(" "), lines };
}

/**
 * @param {ts.SourceFile} file
 * @param {ts.SignatureDeclaration} node
 */
function signature(file, node) {
  const bullets = node.parameters.map((p) => parameter(file, p));
  if (node.type && !ts.isConstructorDeclaration(node)) bullets.push(`* ∟${code(flat(file, node.type))}`);
  return bullets;
}

/**
 * @param {ts.SourceFile} file
 * @param {ts.Node} node
 */
function defined(file, node) {
  const text = node.getText(file).replace(/^export\s+/, "");
  if (!text.includes("\n")) return [code(text)];
  const fence = "`".repeat(Math.max(3, ...(text.match(/`+/g) ?? []).map((run) => run.length + 1)));
  return [`${fence}ts`, ...text.split("\n"), fence];
}

// Policy: a module's surface is what it exports, a class's public members among it, as a Python module's is what
// it names publicly.
/**
 * @param {string} path
 * @param {ts.SourceFile} file
 * @returns {Entry[]}
 */
function surface(path, file) {
  /** @type {Entry[]} */
  const found = [];
  for (const statement of file.statements) {
    if (!exported(statement)) continue;
    const doc = documented(statement);
    if (ts.isFunctionDeclaration(statement) && statement.name) {
      const marks = [
        ...((ts.getModifiers(statement) ?? []).some((m) => m.kind === ts.SyntaxKind.AsyncKeyword)
          ? [code("async")]
          : []),
        ...typed(file, statement.typeParameters),
      ];
      found.push(entry(path, statement.name.text, marks, doc, signature(file, statement)));
    } else if (ts.isClassDeclaration(statement) && statement.name) {
      const name = statement.name.text;
      const marks = [
        ...typed(file, statement.typeParameters),
        ...(statement.heritageClauses ?? []).map((h) => code(flat(file, h))),
      ];
      /** @type {string[]} */
      const fields = [];
      /** @type {Entry[]} */
      const members = [];
      for (const member of statement.members) {
        if (hidden(member)) continue;
        if (ts.isConstructorDeclaration(member)) fields.push(...signature(file, member));
        else if (ts.isPropertyDeclaration(member)) fields.push(`* ${code(flat(file, member).replace(/;$/, ""))}`);
        else if (ts.isMethodDeclaration(member) || ts.isGetAccessorDeclaration(member)) {
          const held = `${name}.${member.name.getText(file)}`;
          members.push(entry(path, held, [], documented(member), signature(file, member)));
        }
      }
      found.push(entry(path, name, marks, doc, fields), ...members);
    } else if (
      (ts.isInterfaceDeclaration(statement) ||
        ts.isTypeAliasDeclaration(statement) ||
        ts.isEnumDeclaration(statement)) &&
      statement.name
    ) {
      const params = ts.isEnumDeclaration(statement) ? undefined : statement.typeParameters;
      found.push(entry(path, statement.name.text, typed(file, params), doc, defined(file, statement)));
    } else if (ts.isVariableStatement(statement)) {
      for (const d of statement.declarationList.declarations) {
        const [name] = bound(d.name);
        if (name === undefined) continue;
        const one = statement.declarationList.declarations.length === 1 && !statement.getText(file).includes("\n");
        let written = name + (d.type ? `: ${flat(file, d.type)}` : "");
        if (d.initializer) written += ` = ${head(file, d.initializer)}`;
        found.push(entry(path, name, [], doc, one ? defined(file, statement) : [code(written)]));
      }
    }
  }
  return found;
}

// Policy: a component's surface is its props, as a function's is its parameters, and what its module script exports.
/**
 * @param {string} path
 * @param {ts.SourceFile} file
 * @returns {Entry[]}
 */
function component(path, file) {
  const name =
    path
      .split("/")
      .at(-1)
      ?.replace(/\.svelte$/, "") ?? path;
  /** @type {string[]} */
  const marks = [];
  /** @type {string[]} */
  const props = [];
  for (const statement of file.statements) {
    if (!ts.isVariableStatement(statement)) continue;
    for (const d of statement.declarationList.declarations) {
      const called = d.initializer && ts.isCallExpression(d.initializer) ? d.initializer.expression : undefined;
      if (!called || !ts.isIdentifier(called) || called.text !== "$props" || !ts.isObjectBindingPattern(d.name))
        continue;
      const literal = d.type && ts.isTypeLiteralNode(d.type) ? d.type : undefined;
      if (d.type && !literal) marks.push(code(flat(file, d.type)));
      for (const e of d.name.elements) {
        const prop = (e.propertyName ?? e.name).getText(file);
        const member = literal?.members.find((m) => m.name?.getText(file) === prop);
        const optional = member && ts.isPropertySignature(member) && member.questionToken ? "?" : "";
        let written = (e.dotDotDotToken ? "..." : "") + prop + optional;
        if (member && ts.isPropertySignature(member) && member.type) written += `: ${flat(file, member.type)}`;
        if (e.initializer) written += ` = ${head(file, e.initializer)}`;
        props.push(`* ${code(written)}`);
      }
    }
  }
  return [entry(path, name, marks, [], props), ...surface(path, file)];
}

/**
 * @param {unknown} node
 * @returns {{ start: number, end: number }[]}
 */
function markup(node) {
  if (Array.isArray(node)) return node.flatMap(markup);
  if (node === null || typeof node !== "object") return [];
  const held = /** @type {Record<string, unknown>} */ (node);
  const own = held.type === "Comment" ? [/** @type {{ start: number, end: number }} */ (held)] : [];
  return [...own, ...Object.values(held).flatMap(markup)];
}

// Accommodating for TypeScript, which reads a component's scripts as a file of their own: what lies outside them is
// blanked but for its newlines, so that a line and a column are the component's.
/**
 * @param {string} path
 * @param {string} source
 * @returns {{ names: Named[], comments: Comment[], surface: Entry[] }}
 */
function svelte(path, source) {
  const root = parse(source, { modern: true });
  // Accommodating for estree's Program, which types no offsets, though Svelte's parser gives them.
  /** @type {{ start: number, end: number }[]} */
  const scripts = [root.module, root.instance].flatMap((s) => (s ? [/** @type {any} */ (s.content)] : []));
  const kept = (/** @type {number} */ i) => scripts.some((s) => s.start <= i && i < s.end);
  const blanked = [...source].map((c, i) => (c === "\n" || kept(i) ? c : " ")).join("");
  const read = typescript(path, blanked);
  const marked = markup(root.fragment).map((c) => comment(source, c.start, c.end));
  return { names: read.names, comments: [...read.comments, ...marked], surface: component(path, read.file) };
}

/** @type {Facts[]} */
const read = process.argv.slice(2).map((path) => {
  const source = readFileSync(path, "utf8");
  const module = path.endsWith(".svelte") ? undefined : typescript(path, source);
  const read = module ? { ...module, surface: surface(path, module.file) } : svelte(path, source);
  const sorted = read.comments.sort((a, b) => a.line - b.line || a.column - b.column);
  return {
    path,
    names: read.names.sort((a, b) => a.line - b.line),
    comments: sorted,
    claims: [],
    surface: read.surface,
  };
});
console.log(JSON.stringify(read));
