Final Critical Reflection Checkpoints

To complete this activity, execute your script and answer these 4 questions in your workspace submission markdown:

1. Which chunking strategy returned the most relevant text for your query? Look closely at the exact string fragment returned—did it capture the entire sentence context or was it cut off?
- fixed size chunking returned the most relevant text, but it was cut off in the middle of the sentence.

2. What happened to the text structure in Fixed-Size Chunk #2 vs. Paragraph Chunk #2? Identify how boundaries changed word availability.
- fixed size Chunk #2 split the sentence mid-way, while Paragraph Chunk #2 kept more complete wording and context.

3. Hypothetical Application: Imagine you are building a production AI system for a company's internal HR manual handbook. Why might relying exclusively on Fixed-Size character chunking create bad answers for employees?
- it can break important policy sentences across chunks and produce incomplete or misleading answers.

4. The Metadata Payload: Why do we spend computing effort storing things like chunk_index and strategy inside the database alongside raw vectors? Why can't we just store the text string alone?
- metadata helps track how each chunk was created and retrieved, which makes searching and debugging easier.
