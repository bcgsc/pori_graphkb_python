const { schema, sentenceTemplates } = require('@bcgsc-pori/graphkb-schema');

const previewFunction = (obj) => schema.getPreview(obj);

// const statement = {
//     displayName: 'displayName',
//     '@class': 'Statement',
//     '@rid': '22:0',
//     displayNameTemplate: 'Given {conditions} {relevance} applies to {subject} ({evidence})',
//     relevance: { displayName: 'Mood Swings', '@rid': '1' },
//     conditions: [{ displayName: 'Low blood sugar', '@class': 'Disease', '@rid': '2'  }],
//     subject: { displayName: 'hungertitis', '@rid': '3', '@class': 'Disease'  },
//     evidence: [{ displayName: 'A reputable source', '@rid': '4'  }],
// };

console.log('################################')
console.log(process.argv[2])
const statement = JSON.parse(process.argv[2])

const { content } = sentenceTemplates.generateStatementSentence(previewFunction, statement);
// Given Low blood sugar Mood Swings applies to hungertitis (A reputable source)

statementLabel = schema.getPreview(content);
console.log(statementLabel)