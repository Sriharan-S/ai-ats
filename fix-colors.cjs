const fs = require('fs');
const path = require('path');

const walk = (dir) => {
  let results = [];
  const list = fs.readdirSync(dir);
  list.forEach((file) => {
    file = path.join(dir, file);
    const stat = fs.statSync(file);
    if (stat && stat.isDirectory()) {
      results = results.concat(walk(file));
    } else {
      if (file.endsWith('.tsx')) {
        results.push(file);
      }
    }
  });
  return results;
};

const files = walk('./src/pages');
files.forEach(file => {
  let content = fs.readFileSync(file, 'utf8');
  content = content.replace(/neutral-/g, 'slate-');
  content = content.replace(/green-/g, 'emerald-');
  content = content.replace(/red-/g, 'rose-');
  content = content.replace(/blue-/g, 'indigo-');
  fs.writeFileSync(file, content);
  console.log('Updated ' + file);
});
