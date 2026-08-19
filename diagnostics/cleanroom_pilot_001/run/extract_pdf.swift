import Foundation
import PDFKit

guard CommandLine.arguments.count == 3 else {
    fputs("usage: extract_pdf.swift INPUT.pdf OUTPUT.txt\n", stderr)
    exit(2)
}

let input = URL(fileURLWithPath: CommandLine.arguments[1])
let output = URL(fileURLWithPath: CommandLine.arguments[2])

guard let document = PDFDocument(url: input) else {
    fputs("unable to open PDF: \(input.path)\n", stderr)
    exit(1)
}

var extracted = ""
for pageIndex in 0..<document.pageCount {
    extracted += "\n===== PDF PAGE \(pageIndex + 1) =====\n"
    if let pageText = document.page(at: pageIndex)?.string {
        extracted += pageText
        if !pageText.hasSuffix("\n") { extracted += "\n" }
    } else {
        extracted += "[NO EXTRACTABLE TEXT]\n"
    }
}

do {
    try extracted.write(to: output, atomically: true, encoding: .utf8)
} catch {
    fputs("unable to write extraction: \(error)\n", stderr)
    exit(1)
}
